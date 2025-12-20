from conan import ConanFile
from conan.tools.env import Environment
from conan.tools.files import copy


class OpenRVRecipe(ConanFile):
    name = "openrv"
    version = "1.0.0"
    python_requires = "openrvcore/1.0.0"
    python_requires_extend = "openrvcore.OpenRVBase"

    settings = "os", "compiler", "build_type", "arch"

    def layout(self):
        super().layout()

    def build_requirements(self):
        super().build_requirements()

    def requirements(self):
        super().requirements()

        disabled_decoders = [
            "bink",
            "binkaudio_dct",
            "binkaudio_rdft",
            "vp9",
            "vp9_cuvid",
            "vp9_mediacodec",
            "vp9_qsv",
            "vp9_rkmpp",
            "vp9_v4l2m2m",
            "dnxhd",
            "prores",
            "qtrle",
            "aac",
            "aac_fixed",
            "aac_latm",
            "dvvideo",
        ]
        disabled_decoders_str = ",".join(disabled_decoders)

        disabled_encoders = [
            "dnxhd",
            "prores",
            "qtrle",
            "aac",
            "aac_mf",
            "vp9_qsv",
            "vp9_vaapi",
            "dvvideo",
        ]
        disabled_encoders_str = ",".join(disabled_encoders)

        disabled_parsers_str = "vp9"
        disabled_filters_str = "geq"
        disabled_protocols_str = "ffrtmpcrypt,rtmpe,rtmpte"

        # TODO Revisit all the options (default options, etc).
        # Prevent the headers and libs of ffmpeg dependencies to be visible downstream.
        self.requires(
            "ffmpeg/6.1.1@openrv",
            transitive_headers=False,
            transitive_libs=False,
            options={
                "with_libiconv": False,
                "with_outdevs": False,
                "with_programs": False,
                "with_large_tests": False,
                "with_doc": False,
                # "with_vulkan": False,  # Disable Vulkan - FFmpeg 6.1.1 has incompatible MESA extensions
                "disable_decoders": disabled_decoders_str,
                "disable_encoders": disabled_encoders_str,
                "disable_parsers": disabled_parsers_str,
                "disable_filters": disabled_filters_str,
                "disable_protocols": disabled_protocols_str,
                "shared": True,
            },
        )

    def generate(self):
        super().generate()

    def build(self):
        super().build()
