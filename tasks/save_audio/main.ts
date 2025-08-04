import type { Context } from "@oomol/types/oocana";
import { FfmpegCommand } from "fluent-ffmpeg";

type Inputs = Readonly<{
  audio_source: FfmpegCommand;
  save_address: string | null;
}>;

type Outputs = Readonly<{ file_adress: string }>;

import { extractBaseName } from "~/utils/get-file-name";
import { getInputPath } from "~/utils/get-input-path";

export default async function (params: Inputs, context: Context): Promise<Outputs> {
  const inputPath = getInputPath(params.audio_source);
  if (!inputPath) {
    throw new Error("Invalid input source: Unable to determine input path.");
  }

  const origin_file_name = extractBaseName(inputPath);
  let save_address: string;
  
  if (params.save_address) {
    if (params.save_address.includes('.')) {
      save_address = params.save_address;
    } else {
      save_address = `${params.save_address}.mp3`;
    }
  } else {
    save_address = `${context.sessionDir}/${origin_file_name}.mp3`;
  }

  console.log(`Input Path: ${inputPath}`);
  console.log(`Output Path: ${save_address}`);

  try {
    await new Promise((resolve, reject) => {
      params.audio_source
        .save(save_address)
        .on("start", (commandLine) => {
          console.log(`FFmpeg started with command: ${commandLine}`);
        })
        .on("end", () => {
          console.log("Conversion complete");
          resolve("ok");
        })
        .on("error", (err, stdout, stderr) => {
          console.error("FFmpeg error:", err.message);
          console.error("FFmpeg stdout:", stdout);
          console.error("FFmpeg stderr:", stderr);
          reject(err);
        });
    });

    console.log("File saved at:", save_address);
    context.preview({ type: "audio", data: save_address });
    return { file_adress: save_address };
  } catch (err) {
    console.error("Error during conversion:", err);
    throw new Error(`Error converting video: ${err.message}`);
  }
}