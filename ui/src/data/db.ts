"use client";
import Dexie, { type EntityTable } from "dexie";

interface File {
  path: string;
  contents: string;
}

interface Workspace {
  name: string;
  template: string;
  dll: string;
}

interface Wallet {
  privateKey: string;
}

const db = new Dexie("aelfAI") as Dexie & {
  files: EntityTable<File, "path">;
  workspaces: EntityTable<Workspace, "name">;
  wallet: EntityTable<Wallet, "privateKey">;
};

// Schema declaration:
db.version(1).stores({
  files: "path, contents",
  workspaces: "name, template, dll",
  wallet: "privateKey",
});

// async function decodeKeys() {
//   return db.transaction('rw', db.files, async () => {
//     const files = await db.files.toArray();

//     for (const file of files) {
//       const decodedId = decodeURIComponent(file.path);

//       // Check if the decoded key already exists to avoid overwriting
//       const existingItem = await db.files.get(decodedId);
//       if (!existingItem) {
//         // Add new item with decoded key
//         await db.files.put({ ...file, path: decodedId });
//         // Delete the old item
//         await db.files.delete(file.path);
//       }
//     }
//   });
// }

db.open()
  .then(() => {
    console.log("Database opened successfully");
    // return decodeKeys();
  })
  .then(() => {
    console.log("Database initialisation complete");
  })
  .catch((err) => {
    console.error("Failed to open db: " + (err.stack || err));
  });

export type { File as FileContent, Workspace, Wallet };
export { db };
