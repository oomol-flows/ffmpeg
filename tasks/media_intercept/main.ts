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
    const { start_time, end_time } = params;
    // const inputPath = getInputPath(params.ffmpeg_source);
    const my_duration = end_time - start_time;
    
    return {ffmpeg_source: params.ffmpeg_source.seekInput(start_time).setDuration(my_duration)}
};
