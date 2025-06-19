import type { Context } from "@oomol/types/oocana";

//#region generated meta
type Inputs = {
    ffmpeg_source: any;
    videoFilter: string;
};
type Outputs = {
    ffmpeg_source: any;
};
//#endregion

export default async function (params: Inputs, context: Context): Promise<Outputs> {
    const ffmpeg_source = params.ffmpeg_source.videoFilter(params.videoFilter)
    return { ffmpeg_source };
};