import type { Context } from "@oomol/types/oocana";
import { FfmpegCommand } from "fluent-ffmpeg";

type Inputs = Readonly<{
  video_source: FfmpegCommand,
  file_name: string | null,
  format: string | null,
  save_address: string | null,
}>;

type Outputs = Readonly<{ file_adress: string }>;
import { extractBaseName } from "~/utils/get-file-name"
import { getInputPath } from "~/utils/get-input-path";


export default async function (params: Inputs, context: Context): Promise<Outputs> {

  const inputPath = getInputPath(params.video_source);
  const origin_file_name = extractBaseName(inputPath);
  const file_name = params.file_name ? params.file_name : origin_file_name;
  const formate = params.format ? params.format : "mp4";
  const save_address = params.save_address 
    ? `${params.save_address}/${file_name}.${formate}` 
    : `${context.sessionDir}/output-${file_name}.${formate}` // Add 'output-' prefix to avoid overwriting input
  try {
    await new Promise((resolve, reject) => {
      params.video_source
        .save(save_address)
        .on("start", (commandLine) => {
          console.log(`FFmpeg started with command: ${commandLine}`);
        })
        .on("end", () => {
          resolve("ok");
        })
        .on('error', (err) => {
          console.log("ffmpeg error")
          reject(err);
        });
    });
    console.log('Conversion complete');
  } catch (err) {
    console.error('Error during conversion:', err);
    throw new Error(`Error converting video: ${err}`);
  } finally {
    console.log(save_address);
    context.preview({ type: "video", data: save_address })
    return { file_adress: save_address };
  }
};