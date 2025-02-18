"use client";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

import { NewFileForm } from "./new-file-form";

export default function NewFile({
  defaultPath,
  isOpen,
  setIsOpen,
}: React.PropsWithChildren<{
  defaultPath?: string;
  isOpen: boolean;
  setIsOpen: (open: boolean) => void;
}>) {
  return (
    <Dialog open={isOpen} onOpenChange={(open) => setIsOpen(open)}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="mb-4">New File</DialogTitle>
          <DialogDescription>
            <NewFileForm defaultPath={defaultPath} onSubmit={() => setIsOpen(false)} />
          </DialogDescription>
        </DialogHeader>
      </DialogContent>
    </Dialog>
  );
}
