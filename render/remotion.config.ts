import { Config } from "@remotion/cli/config";

Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);
// Use the GPU encoder when available; falls back automatically if not.
Config.setCodec("h264");
