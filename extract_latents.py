import argparse
import os
import torch
import torch.distributed as dist
from torch.utils.data import DataLoader
torch.backends.cudnn.benchmark = True
from tqdm import tqdm
import logging
from data_utils.v2a_utils.vggsound_224_no_audio import VGGSound
from data_utils.v2a_utils.feature_utils_224 import FeaturesUtils as OriginalFeatures
import numpy as np
from huggingface_hub import hf_hub_download
from torch.utils.data.dataloader import default_collate
import time
import gc

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def error_avoidance_collate(batch):
    batch = list(filter(lambda x: x is not None, batch))
    return default_collate(batch)

# GPU memory print helper
def print_gpu(stage=""):
    if torch.cuda.is_available():
        alloc = torch.cuda.memory_allocated() / 1024**2
        reserved = torch.cuda.memory_reserved() / 1024**2
        logger.info(f"[{stage}] GPU Allocated: {alloc:.1f} MB, Reserved: {reserved:.1f} MB")
    else:
        logger.info(f"[{stage}] CUDA not available")

def warmup_models(extractor):
    """Warm up models with dummy data to prevent hanging"""
    logger.info("Warming up models...")
    
    if torch.cuda.is_available():
        device = torch.device('cuda')
        dtype = torch.float16 if extractor.use_half else torch.float32
        
        # Warm up CLIP
        dummy_clip = torch.randn(1, 3, 224, 224, device=device, dtype=dtype)
        _ = extractor.encode_video_with_clip(dummy_clip)
        torch.cuda.empty_cache()
        
        # Warm up Synchformer
        dummy_sync = torch.randn(1, 3, 16, 224, 224, device=device, dtype=dtype)
        _ = extractor.encode_video_with_sync(dummy_sync)
        torch.cuda.empty_cache()
        
        # Warm up text encoders
        dummy_text = ["test caption"]
        _ = extractor.encode_text(dummy_text)
        _ = extractor.encode_t5_text(dummy_text)
        torch.cuda.empty_cache()
        
        logger.info("✅ Models warmed up successfully")
    else:
        logger.info("⚠️  CUDA not available, skipping warmup")

def main(args):
    logger.info("Starting extract_latents.py...")
    logger.info(f"Arguments: {args}")
    
    # Check CUDA availability
    if torch.cuda.is_available():
        logger.info(f"CUDA available: {torch.cuda.get_device_name(0)}")
    else:
        logger.warning("CUDA not available, using CPU")
    
    # Dataset
    logger.info("Loading dataset...")
    dataset = VGGSound(
        root=args.root,
        tsv_path=args.tsv_path,
        sample_rate=args.sample_rate,
        duration_sec=args.duration_sec,
        audio_samples=args.audio_samples,
        start_row=args.start_row,
        end_row=args.end_row,
        save_dir=args.save_dir
    )
    
    if len(dataset) == 0:
        logger.error("Dataset is empty! Check your TSV file and root directory.")
        return
    
    logger.info(f"Dataset loaded with {len(dataset)} samples")
    os.makedirs(args.save_dir, exist_ok=True)

    # DataLoader with timeout to prevent hanging
    dataloader = DataLoader(
        dataset,
        batch_size=2,
        num_workers=0,  # Use 0 to prevent multiprocessing issues
        pin_memory=False,
        drop_last=False,
        collate_fn=error_avoidance_collate,
        timeout=300  # 5 minute timeout
    )

    # Initialize feature extractor
    logger.info("Initializing feature extractor...")
    extractor = FeaturesUtils(
        vae_ckpt=None,
        vae_config=None,
        enable_conditions=True,
        synchformer_ckpt=args.synchformer_ckpt,
        use_half=args.use_half
    )
    
    # Warm up models
    warmup_models(extractor)
    
    logger.info("Starting processing...")
    processed_count = 0
    
    try:
        for i, data in enumerate(tqdm(dataloader, desc="Processing", unit="batch")):
            ids = data['id']
            
            try:
                with torch.no_grad():
                    output = {
                        'caption': str(data['caption']),
                        'caption_cot': str(data['caption_cot'])
                    }

                    # Process CLIP features
                    clip_video = data['clip_video']
                    clip_features = extractor.encode_video_with_clip(clip_video)
                    output['metaclip_features'] = clip_features

                    # Process Synchformer features
                    sync_video = data['sync_video']
                    sync_features = extractor.encode_video_with_sync(sync_video)
                    output['sync_features'] = sync_features

                    # Process text features
                    caption = data['caption']
                    metaclip_global_text_features, metaclip_text_features = extractor.encode_text(caption)
                    output['metaclip_global_text_features'] = metaclip_global_text_features
                    output['metaclip_text_features'] = metaclip_text_features

                    # Process T5 features
                    caption_cot = data['caption_cot']
                    t5_features = extractor.encode_t5_text(caption_cot)
                    output['t5_features'] = t5_features

                    # Save each sample
                    for j in range(len(ids)):
                        sample_output = {
                            'id': ids[j],
                            'caption': output['caption'][j] if isinstance(output['caption'], list) else str(output['caption']),
                            'caption_cot': output['caption_cot'][j] if isinstance(output['caption_cot'], list) else str(output['caption_cot']),
                            'metaclip_features': output['metaclip_features'][j],
                            'sync_features': output['sync_features'][j],
                            'metaclip_global_text_features': output['metaclip_global_text_features'][j],
                            'metaclip_text_features': output['metaclip_text_features'][j],
                            't5_features': output['t5_features'][j],
                        }
                        
                        # Convert tensors to numpy arrays
                        for k, v in sample_output.items():
                            if isinstance(v, torch.Tensor):
                                sample_output[k] = v.float().cpu().numpy()
                        
                        np.savez(f'{args.save_dir}/{ids[j]}.npz', **sample_output)
                        processed_count += 1
                        
                        # Log progress every 10 samples
                        if processed_count % 10 == 0:
                            logger.info(f"Processed {processed_count} samples")
                            print_gpu(f"batch_{i}_sample_{j}")
                
            except Exception as e:
                logger.error(f"Error processing batch {i}: {str(e)}")
                logger.error(f"IDs in failed batch: {ids}")
                continue
            
            # Force garbage collection
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
    
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error during processing: {str(e)}")
        raise
    
    logger.info(f"Processing complete! Total samples processed: {processed_count}")
    print_gpu("finished")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', default='videos')
    parser.add_argument('--tsv_path', default='cot_coarse/cot.csv')
    parser.add_argument('--save-dir', default='results')
    parser.add_argument('--sample_rate', type=int, default=44100)
    parser.add_argument('--duration_sec', type=float, default=9.0)
    parser.add_argument('--synchformer_ckpt', default='ckpts/synchformer_state_dict.pth')
    parser.add_argument('--start-row', type=int, default=0)
    parser.add_argument('--end-row', type=int, default=None)
    parser.add_argument('--use_half', action='store_true', help='Use half precision for models to save memory')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    args.audio_samples = int(args.sample_rate * args.duration_sec)
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    main(args)
