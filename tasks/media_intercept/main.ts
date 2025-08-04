//#region generated meta
type Inputs = {
    ffmpeg_source: any;
    start_time: number;
    end_time: number;
};
type Outputs = {
    ffmpeg_source: any;
};
//#endregion

import type { Context } from "@oomol/types/oocana";
import {getInputPath} from "~/utils/get-input-path";

export default async function (
    params: Inputs,
    context: Context<Inputs, Outputs>
): Promise<Partial<Outputs> | undefined | void> {
    const { ffmpeg_source, start_time, end_time } = params;
    const inputPath = getInputPath(params.ffmpeg_source);
    const cloned_ffmpeg = ffmpeg_source.clone().input(inputPath);
    const my_duration = end_time - start_time;
    
    cloned_ffmpeg.seekInput(start_time).setDuration(my_duration);
    
    return {ffmpeg_source: cloned_ffmpeg}
};
