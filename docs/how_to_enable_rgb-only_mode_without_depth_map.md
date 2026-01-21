The original FoundationPose code and NGC model do not expose an official “RGB‑only mode”; they expect RGBD plus intrinsics and a CAD (or neural field), so you must either hack the inputs (e.g., zero‑depth) or adopt an RGB‑only derivative such as RGBTrack. [arxiv](https://arxiv.org/pdf/2506.17119.pdf)

## What FoundationPose expects

- The public model card and docs state that the model takes an image, a **depth map**, and a 3D model (or RGBD exemplars) as inputs for pose and tracking; depth is part of the standard interface. [nvlabs.github](https://nvlabs.github.io/FoundationPose/)
- GitHub issues clarify that all listed inputs (RGB, depth, bbox, CAD, intrinsics) are required together, not “any one of them”, so RGB alone is not a supported configuration in the official implementation. [github](https://github.com/NVlabs/FoundationPose/issues/300)

## Trick: zero‑depth input

- RGBTrack shows that you can feed a **zero-depth matrix** into FoundationPose’s refinement stage and still obtain usable tracking, because RefineNet falls back to relying entirely on RGB features when depth features vanish. [arxiv](https://arxiv.org/html/2506.17119v1)
- Concretely, this means:  
  - Keep the same input pipeline (RGBD image, intrinsics, CAD, etc.).  
  - Replace the depth channel with an all‑zero image (or a constant plane) at the expected resolution and scale before converting it to a point cloud.  
  - Run the normal refinement/selection steps; the network treats point‑cloud channels as degenerate, and effectively operates as an RGB‑only relative pose refiner. [arxiv](https://arxiv.org/pdf/2506.17119.pdf)

## Using RGBTrack instead

- RGBTrack “builds upon FoundationPose” and provides a full **depth‑free** pipeline: it gets an initial pose, then uses a binary search plus render‑and‑compare strategy with the CAD model to infer depth and refine poses from RGB only. [papers](https://papers.cool/arxiv/2506.17119)
- If you want a maintained, code‑level solution rather than a custom hack, using RGBTrack (or similar RGB‑only extensions) is currently the most practical way to get FoundationPose‑style behavior without a depth map. [arxiv](https://arxiv.org/abs/2506.17119)

## Practical guidance

- For quick experiments:  
  - Use NVIDIA’s FoundationPose demo, but inject a zero‑depth image at the point where the RGBD frame is assembled; ensure intrinsics and CAD scale are still correct. [catalog.ngc.nvidia](https://catalog.ngc.nvidia.com/orgs/nvidia/teams/isaac/models/foundationpose)
- For a robust system:  
  - Start from RGBTrack’s codebase, which already wraps FoundationPose‑like networks for RGB‑only 6D pose estimation and tracking and handles drift, recovery, and scale adaptation from CAD. [github](https://github.com/GreatenAnoymous/RGBTrack)