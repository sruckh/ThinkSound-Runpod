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
# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def error_avoidance_collate(batch):
    batch = list(filter(lambda x: x is not None, batch))
    return default_collate(batch)

# GPU memory print helper
def print_gpu(stage=""):
    alloc = torch.cuda.memory_allocated() / 1024**2
    reserved = torch.cuda.memory_reserved() / 1024**2
    logging.info(f"[{stage}] GPU Allocated: {alloc:.1f} MB, Reserved: {reserved:.1f} MB")

# Distributed setup

def setup(rank, world_size):
    dist.init_process_group("nccl", rank=rank, world_size=world_size)
    torch.cuda.set_device(rank)

def cleanup():
    dist.destroy_process_group()

def main(args):
    #print_gpu("startup")
    # Dataset
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
    os.makedirs(args.save_dir, exist_ok=True)

    # DataLoader
    dataloader = DataLoader(
        dataset,
        batch_size=1,
        num_workers=2,
        pin_memory=False,
        drop_last=False,
        collate_fn=error_avoidance_collate
    )

    # Lazy feature extractor
    class FeaturesUtils(OriginalFeatures):
        def __init__(self, *a,use_half=True, **kw):
            super().__init__(*a, **kw)
            self.use_half = use_half
            if self.use_half:
                logging.info("Using half precision for models to save memory")
            # initially offload heavy modules
            if self.clip_model is not None:
                self.clip_model.to('cpu')
                if self.use_half:
                    self.clip_model = self.clip_model.half()
            if hasattr(self, 't5_model') and self.t5_model is not None:
                self.t5_model.to('cpu')
                if self.use_half:
                    self.t5_model = self.t5_model.half()
            if self.synchformer is not None:
                self.synchformer.to('cpu')
                if self.use_half:
                    self.synchformer = self.synchformer.half()
            #print_gpu("models_offloaded")

        def _load_to_cuda(self, model):
            if self.use_half:
                model = model.half()
            return model.to('cuda')

        @torch.inference_mode()
        def encode_video_with_clip(self, x, batch_size=-1):
            # load and offload
            model = self._load_to_cuda(self.clip_model)
            out = super().encode_video_with_clip(x.to('cuda'), batch_size)
            model.to('cpu')
            torch.cuda.empty_cache()
            #print_gpu("after_clip")
            return out

        @torch.inference_mode()
        def encode_video_with_sync(self, x, batch_size=-1):
            model = self._load_to_cuda(self.synchformer)
            x = x.to('cuda')
            if self.use_half:
                x = x.half()
            out = super().encode_video_with_sync(x, batch_size)
            model.to('cpu')
            torch.cuda.empty_cache()
            #print_gpu("after_sync")
            return out

        @torch.inference_mode()
        def encode_text(self, text_list):
            model = self._load_to_cuda(self.clip_model)
            out = super().encode_text(text_list)
            model.to('cpu')
            torch.cuda.empty_cache()
            #print_gpu("after_text")
            return out

        @torch.inference_mode()
        def encode_t5_text(self, text_list):
            tokenizer = self.t5_tokenizer
            # load t5
            model = self._load_to_cuda(self.t5_model)
            inputs = tokenizer(text_list, truncation=True, max_length=77,
                               padding='max_length', return_tensors='pt').to('cuda')
            out = model(**inputs).last_hidden_state.cpu()
            model.to('cpu')
            torch.cuda.empty_cache()
            #print_gpu("after_t5")
            return out

    # Initialize new extractor
    extractor = FeaturesUtils(
        vae_ckpt=None,
        vae_config=None,
        enable_conditions=True,
        synchformer_ckpt=args.synchformer_ckpt,
        use_half=args.use_half
    )

    #print_gpu("models_initialized")

    for i, data in enumerate(tqdm(dataloader, desc="Processing", unit="batch")):
        # 使用 torch.no_grad() 来加快推理速度
        ids = data['id']  # 获取当前批次的所有 ID
        with torch.no_grad():
            # audio = data['audio'].cuda(rank, non_blocking=True)
            output = {
                'caption': str(data['caption']),
                'caption_cot': str(data['caption_cot'])
            }
            print(output)
            # logging.info(f'Processing batch {i} with IDs: {ids}')  # 添加日志记录

            # latent = feature_extractor.module.encode_audio(audio)
            # output['latent'] = latent.detach().cpu()

            clip_video = data['clip_video']
            # logging.info(f'Processing batch {i} with shape: {clip_video.shape}')  # 添加日志记录
            clip_features = extractor.encode_video_with_clip(clip_video)
            output['metaclip_features'] = clip_features

            sync_video = data['sync_video']
            sync_features = extractor.encode_video_with_sync(sync_video)
            output['sync_features'] = sync_features

            caption = data['caption']
            metaclip_global_text_features, metaclip_text_features = extractor.encode_text(caption)
            output['metaclip_global_text_features'] = metaclip_global_text_features
            output['metaclip_text_features'] = metaclip_text_features

            caption_cot = data['caption_cot']
            t5_features = extractor.encode_t5_text(caption_cot)
            output['t5_features'] = t5_features


            # 保存每个样本的输出
            for j in range(len(ids)):
                sample_output = {
                    'id': ids[j],
                    'caption': output['caption'][j],
                    'caption_cot': output['caption_cot'][j],
                    # 'latent': output['latent'][j],
                    'metaclip_features': output['metaclip_features'][j],
                    'sync_features': output['sync_features'][j],
                    'metaclip_global_text_features': output['metaclip_global_text_features'][j],
                    'metaclip_text_features': output['metaclip_text_features'][j],
                    't5_features': output['t5_features'][j],
                }
                for k, v in sample_output.items():
                    if isinstance(v, torch.Tensor):
                        sample_output[k] = v.float().cpu().numpy()
                # torch.save(sample_output, f'{save_dir}/{ids[j]}.pth')
                np.savez(f'{args.save_dir}/demo.npz', **sample_output)

    #print_gpu("finished")

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
    args = parser.parse_args()
    args.audio_samples = int(args.sample_rate * args.duration_sec)
    #args.synchformer_ckpt = hf_hub_download(repo_id="liuhuadai/ThinkSound", filename="synchformer_state_dict.pth")
    main(args)
