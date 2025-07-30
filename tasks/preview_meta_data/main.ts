import type { Context } from "@oomol/types/oocana";
import ffmpeg, { FfmpegCommand } from "fluent-ffmpeg";
import { promisify } from "node:util"
import { getInputPath } from "~/utils/get-input-path";
const ffprobe = promisify(ffmpeg.ffprobe);

type Inputs = {
  ffmpeg_source: FfmpegCommand;
}
type Outputs = {
  ffmpeg_source: FfmpegCommand;
  meta_data: string;
}

export default async function(
  params: Inputs,
  context: Context<Inputs, Outputs>
): Promise<Outputs> {
  const {ffmpeg_source} = params;
  const inputPath = getInputPath(params.ffmpeg_source);
  const metadata = await ffprobe(inputPath);
  if (metadata){
    context.preview({
      type: "json",
      data: metadata
    })
  }

  return { ffmpeg_source: ffmpeg_source, meta_data: JSON.stringify(metadata) as string };
};
