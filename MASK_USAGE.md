# Mask Usage for Tracking

## Default Behavior

**Masks are enabled by default** - no flag needed!

The code automatically uses masks for all frames if mask files exist in the `masks/` directory. If masks are not available, it gracefully falls back to tracking without masks.

## How It Works

### Default (Masks Enabled)
```bash
# Masks are automatically used if available
python run.py --inputs /path/to/data
```

**Behavior:**
- ✅ Tries to load masks for all frames from `masks/` directory
- ✅ Uses masks during tracking if found
- ✅ Falls back to tracking without masks if mask files are missing
- ✅ No errors if masks don't exist

### Disable Masks
```bash
# Explicitly disable mask usage
python run.py --inputs /path/to/data --no_masks
```

**Behavior:**
- ❌ Skips mask loading entirely
- ❌ Tracks without masks for all frames
- ✅ Useful for testing or when masks are not available

## Command Line Options

| Option | Default | Description |
|--------|---------|-------------|
| *(none)* | `True` | Masks enabled by default - automatically used if available |
| `--no_masks` | - | Disable mask usage - track without masks even if mask files exist |

## Examples

### Using Masks (Default)
```bash
# Masks will be used automatically if available
python run.py --inputs ./user/mustard0_rgb/inputs --rgb_only
```

### Disabling Masks
```bash
# Force tracking without masks
python run.py --inputs ./user/mustard0_rgb/inputs --rgb_only --no_masks
```

### Comparison Script
The comparison script (`experiments/compare_mask_tracking.py`) has its own `use_mask` parameter:
```bash
# Compare with and without masks
python experiments/compare_mask_tracking.py \
    --inputs ./user/mustard0_rgb/inputs \
    --outputs ./experiments/results/comparison
```

## Directory Structure

For masks to be automatically detected:
```
input_directory/
├── rgb/              # RGB images
│   ├── 000000.png
│   ├── 000001.png
│   └── ...
├── masks/            # Mask images (same filenames as rgb/)
│   ├── 000000.png
│   ├── 000001.png
│   └── ...
└── cam_K.txt         # Camera intrinsics
```

## Implementation Details

- **Registration (Frame 0)**: Always uses mask if available (required for initialization)
- **Tracking (Frames 1+)**: Uses masks if `--no_masks` flag is NOT used
- **Fallback**: If mask file is missing, automatically falls back to tracking without mask
- **Backward Compatible**: Existing code works without modification

## Summary

- ✅ **Default**: Masks enabled (no flag needed)
- ✅ **Automatic**: Masks used if files exist
- ✅ **Graceful**: Falls back if masks missing
- ✅ **Optional**: Use `--no_masks` to disable
