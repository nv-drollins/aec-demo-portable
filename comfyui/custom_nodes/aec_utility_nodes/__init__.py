# AEC Utility Nodes — SimpleInpaintCrop + SimpleInpaintStitch + ColorCode

import torch
import torch.nn.functional as F
import json


class SimpleInpaintCrop:
    """Crops image + mask to the bounding box of the masked region for inpainting."""
    CATEGORY = "AEC/inpaint"
    RETURN_TYPES = ("IMAGE", "MASK", "IMAGE", "STRING", "STRING")
    RETURN_NAMES = ("cropped_image", "cropped_mask", "masked_composite", "bbox_data", "info")
    FUNCTION = "crop"

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "image":   ("IMAGE",),
            "mask":    ("MASK",),
            "padding": ("INT",     {"default": 0, "min": 0, "max": 256}),
            "blur":    ("BOOLEAN", {"default": False}),
        }}

    def crop(self, image, mask, padding=0, blur=False):
        if mask.dim() == 2:
            mask = mask.unsqueeze(0)
        B, H, W, C = image.shape
        m = mask[0]
        nonzero = torch.nonzero(m > 0.5)
        if nonzero.numel() == 0:
            x0, y0, x1, y1 = 0, 0, W, H
        else:
            y0 = max(0, int(nonzero[:, 0].min()) - padding)
            y1 = min(H, int(nonzero[:, 0].max()) + 1 + padding)
            x0 = max(0, int(nonzero[:, 1].min()) - padding)
            x1 = min(W, int(nonzero[:, 1].max()) + 1 + padding)
        cropped_img  = image[:, y0:y1, x0:x1, :]
        cropped_mask = mask[:,  y0:y1, x0:x1]
        composite    = image.clone()
        composite[:, y0:y1, x0:x1, :] *= (1 - cropped_mask.unsqueeze(-1))
        bbox_data = json.dumps({"x0": x0, "y0": y0, "x1": x1, "y1": y1,
                                "orig_w": W, "orig_h": H})
        info = f"Cropped {x1-x0}x{y1-y0} from {W}x{H} at ({x0},{y0})"
        return (cropped_img, cropped_mask, composite, bbox_data, info)


class SimpleInpaintStitch:
    """Pastes a processed crop back into the original image at the location
    recorded by SimpleInpaintCrop's bbox_data, feathering the blend edge with
    blend_mask (the crop's own mask, resized to match the crop as needed).

    NOTE: this node was missing from the bundled package even though the AEC
    workflow graph requires it (3 SimpleInpaintStitch nodes reference it) -
    added here to match SimpleInpaintCrop's bbox_data contract exactly. Not
    the original author's implementation (none shipped with this drop), so
    sanity-check output quality against your own inpaint-crop/stitch nodes
    if you have a reference to compare.
    """
    CATEGORY = "AEC/inpaint"
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "stitch"

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "original_image": ("IMAGE",),
            "processed_crop": ("IMAGE",),
            "bbox_data":      ("STRING", {"default": ""}),
            "blend_mode":     (["blend", "replace"], {"default": "blend"}),
            "feather":        ("INT", {"default": 0, "min": 0, "max": 256}),
        },
        "optional": {
            "blend_mask": ("MASK",),
        }}

    def stitch(self, original_image, processed_crop, bbox_data, blend_mode="blend", feather=0, blend_mask=None):
        data = json.loads(bbox_data)
        x0, y0, x1, y1 = data["x0"], data["y0"], data["x1"], data["y1"]
        out = original_image.clone()
        crop_h, crop_w = y1 - y0, x1 - x0

        pc = processed_crop
        if pc.shape[1] != crop_h or pc.shape[2] != crop_w:
            pc = F.interpolate(pc.permute(0, 3, 1, 2), size=(crop_h, crop_w),
                                mode="bilinear", align_corners=False).permute(0, 2, 3, 1)

        if blend_mode == "replace" or blend_mask is None:
            out[:, y0:y1, x0:x1, :] = pc
            return (out,)

        m = blend_mask
        if m.dim() == 2:
            m = m.unsqueeze(0)
        if m.shape[1] != crop_h or m.shape[2] != crop_w:
            m = F.interpolate(m.unsqueeze(1), size=(crop_h, crop_w),
                               mode="bilinear", align_corners=False).squeeze(1)
        if feather > 0:
            k = feather * 2 + 1
            m = F.avg_pool2d(m.unsqueeze(1), kernel_size=k, stride=1, padding=feather).squeeze(1)
        m = m.unsqueeze(-1)

        region = out[:, y0:y1, x0:x1, :]
        out[:, y0:y1, x0:x1, :] = region * (1 - m) + pc * m
        return (out,)


class ColorCode:
    """Colour picker — outputs hex string, RGB string, RGBA string, and alpha float."""
    CATEGORY = "AEC/color"
    RETURN_TYPES = ("STRING", "STRING", "STRING", "FLOAT")
    RETURN_NAMES = ("hex", "rgb", "rgba", "alpha")
    FUNCTION = "color_code"

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "hex_color": ("STRING",  {"default": "#FFFFFF"}),
            "alpha":     ("FLOAT",   {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01}),
        }}

    def color_code(self, hex_color="#FFFFFF", alpha=1.0):
        h = hex_color.lstrip("#")
        if len(h) == 6:
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        else:
            r, g, b = 255, 255, 255
        rgb  = f"{r}, {g}, {b}"
        rgba = f"{r}, {g}, {b}, {int(alpha * 255)}"
        return (hex_color, rgb, rgba, float(alpha))


NODE_CLASS_MAPPINGS = {
    "SimpleInpaintCrop":   SimpleInpaintCrop,
    "SimpleInpaintStitch": SimpleInpaintStitch,
    "ColorCode":           ColorCode,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "SimpleInpaintCrop":   "Simple Inpaint Crop",
    "SimpleInpaintStitch": "Simple Inpaint Stitch",
    "ColorCode":           "Color Code",
}

print("[AEC Utility Nodes] Loaded: SimpleInpaintCrop, SimpleInpaintStitch, ColorCode")
