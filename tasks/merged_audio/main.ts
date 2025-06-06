import type { Context } from "@oomol/types/oocana";
import ffmpeg from "fluent-ffmpeg";

type Inputs = {
  audio_files: string[];
  name: string | null;
  format: string | null;
  save_address: string | null;
}
type Outputs = {
  save_address: string;
}

export default async function (
  params: Inputs,
  context: Context<Inputs, Outputs>
): Promise<Outputs> {
  const { audio_files, name, format, save_address } = params
  const audio_name = name || 'merged_audio';
  const audio_format = format || 'mp3';
  const tempDir = save_address || context.sessionDir;
  const outputFile = `${tempDir}/${audio_name}.${audio_format}`;


  try {
    await mergeMP3Files(audio_files, outputFile, context.sessionDir);
    console.log('Files merged successfully:', outputFile);
  } catch (err) {
    console.error('Merge failed:', err.message);
  }

  return { save_address: outputFile };
};

// 合并 MP3 文件的异步函数
async function mergeMP3Files(inputFiles: string[], outputFile: string, tempDir: string) {
  return new Promise((resolve, reject) => {
    const command = ffmpeg();

    // 添加输入文件
    inputFiles.forEach(file => command.input(file));

    // 合并文件
    command
      .on("start", (commandLine) => {
        console.log(`FFmpeg started with command: ${commandLine}`);
      })
      .on('end', () => resolve(outputFile))
      .on('error', (err) => reject(err))
      .mergeToFile(outputFile, tempDir);
  });
}