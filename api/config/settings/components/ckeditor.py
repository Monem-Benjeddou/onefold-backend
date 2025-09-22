"""
CKEditor configurations.
"""

CKEDITOR_UPLOAD_PATH = "uploads/"
CKEDITOR_IMAGE_BACKEND = "pillow"

CKEDITOR_CONFIGS = {
    "default": {
        "toolbar": "full",
        "height": 300,
        "width": "100%",
    },
    "courses": {
        "toolbar": [
            ["Bold", "Italic", "Underline", "Strike", "Subscript", "Superscript"],
            ["NumberedList", "BulletedList", "Blockquote"],
            ["JustifyLeft", "JustifyCenter", "JustifyRight", "JustifyBlock"],
            ["Link", "Unlink", "Anchor"],
            ["Image", "Table", "HorizontalRule", "SpecialChar"],
            ["Styles", "Format", "Font", "FontSize"],
            ["TextColor", "BGColor"],
            ["Maximize", "ShowBlocks", "Source"],
        ],
        "height": 500,
        "width": "100%",
        "extraPlugins": ",".join(
            [
                "codesnippet",
                "youtube",
                "uploadimage",
                "prism",
                "widget",
                "lineutils",
            ]
        ),
    },
}
