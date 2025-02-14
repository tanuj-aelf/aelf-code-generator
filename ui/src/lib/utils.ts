import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"
import JSZip from 'jszip';
import { saveAs } from 'file-saver';
import { FolderStructure } from "@/types";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export async function downloadAsZip(folderStructure: FolderStructure, projectName: string = 'aelf-contract') {
  const zip = new JSZip();
  
  // Recursive function to add files to zip
  const addToZip = (structure: FolderStructure, parentFolder: JSZip) => {
    Object.entries(structure).forEach(([path, content]) => {
      if (typeof content === 'string') {
        // It's a file
        parentFolder.file(path, content);
      } else {
        // It's a folder
        const folder = parentFolder.folder(path);
        if (folder) {
          addToZip(content, folder);
        }
      }
    });
  };

  // Add all files to zip
  addToZip(folderStructure, zip);

  // Generate and download the zip file
  const zipContent = await zip.generateAsync({ type: 'blob' });
  saveAs(zipContent, `${projectName}.zip`);
} 