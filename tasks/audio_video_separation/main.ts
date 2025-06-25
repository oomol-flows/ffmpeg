import type { Context } from "@oomol/types/oocana";
import {FfmpegCommand} from "fluent-ffmpeg";
import { getInputPath } from "~/utils/get-input-path";

type Inputs = Readonly<{ 
  ffmpeg_source: FfmpegCommand,
 }>;
type Outputs = Readonly<{
  only_video: FfmpegCommand,
  only_audio: FfmpegCommand,
}>;

export default async function(params: Inputs, context: Context): Promise< Outputs> {
  const inputPath = getInputPath(params.ffmpeg_source);
  const video = params.ffmpeg_source.clone().input(inputPath).noAudio();
  const audio = params.ffmpeg_source.clone().input(inputPath).noVideo();


  return { only_video: video, only_audio: audio};
};