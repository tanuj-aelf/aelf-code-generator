"use client";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "../ui/button";
import { usePathname } from "next/navigation";
import { useRefreshFileExplorer } from "./FileExplorer";
import { db } from "@/data/db";

export default function Delete({
  type,
  path,
  isOpen,
  setIsOpen,
}: React.PropsWithChildren<{
  type?: "file" | "folder";
  path?: string;
  isOpen: boolean;
  setIsOpen: (open: boolean) => void;
}>) {
  const pathName = usePathname().replace("/", "");
  const refreshFileExplorer = useRefreshFileExplorer();

  if (!path) return null;

  const handleDelete = async () => {
    if (type === "file") {
      await db.files.delete(`/workspace/${pathName}/${path}`);
    } else {
      const all = (
        await db.files
          .filter((file) =>
            file.path.startsWith(`/workspace/${pathName}/${path}/`)
          )
          .toArray()
      ).map((i) => i.path);
      await db.files.bulkDelete(all);
    }

    await refreshFileExplorer();
    setIsOpen(false);
  };
  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="mb-4">Delete {type}</DialogTitle>
          <DialogDescription>
            Are you sure you want to delete {path} ? <br />
            This action is not reversible!
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button
            variant="outline"
            className="w-full"
            onClick={() => setIsOpen(false)}
          >
            Cancel
          </Button>
          <Button
            variant="ghost"
            className="w-full bg-white text-black"
            onClick={handleDelete}
          >
            Confirm
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
