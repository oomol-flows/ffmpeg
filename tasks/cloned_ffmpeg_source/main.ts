import type { Context } from "@oomol/types/oocana";
import {FfmpegCommand} from "fluent-ffmpeg";
import {getInputPath} from "~/utils/get-input-path";

type Inputs = Readonly<{ 
  ffmpeg_source: FfmpegCommand,
 }>;
type Outputs = Readonly<{
  cloned_ffmpeg: FfmpegCommand,
}>;


export default async function(
  params: Inputs,
  context: Context<Inputs, Outputs>
): Promise<Outputs> {
  const inputPath = getInputPath(params.ffmpeg_source);
  const cloned_ffmpeg = params.ffmpeg_source.clone().input(inputPath); 
  return { cloned_ffmpeg: cloned_ffmpeg };
};
