import { FileContent } from "@/data/db";
import { Zippable, strToU8, zipSync } from "fflate";

export function fileContentToZip(files: FileContent[]) {
  const zipFiles: Zippable = files.reduce((acc, { path, contents }) => {
    acc[path] = strToU8(contents);

    return acc;
  }, {} as Zippable);

  const zippedData = zipSync(zipFiles);
  return zippedData;
}
