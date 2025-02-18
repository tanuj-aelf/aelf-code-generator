"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Loader2 } from "lucide-react";
import { Input } from "../ui/input";
import { usePathname } from "next/navigation";
import { db } from "@/data/db";
import { useRefreshFileExplorer } from "./FileExplorer";

const FormSchema = z.object({
  path: z.string(),
});

export function RenameForm({
  onSubmit,
  type,
  path,
}: {
  onSubmit?: (path: string) => void;
  type?: "file" | "folder";
  path?: string;
}) {
  const pathName = usePathname().replace("/", "");
  const refreshFileExplorer = useRefreshFileExplorer();

  const form = useForm<z.infer<typeof FormSchema>>({
    resolver: zodResolver(FormSchema),
    defaultValues: {
      path,
    },
  });

  async function _onSubmit(data: z.infer<typeof FormSchema>) {
    form.clearErrors();

    if (!path) return;

    try {
      const currentKey = `/workspace/${pathName}/${path}`;
      const newKey = `/workspace/${pathName}/${data.path}`;

      if (type === "file") {
        
        const currentFile = await db.files.get(currentKey);
        await db.files.add({
          path: newKey,
          contents: currentFile?.contents || "",
        });
        await db.files.delete(currentKey);
      } else {
        const currentFiles = await db.files
          .filter((file) => file.path.startsWith(currentKey))
          .toArray();

        const newFiles = currentFiles.map((i) => ({
          ...i,
          path: i.path.replace(currentKey, newKey),
        }));

        await db.files.bulkAdd(newFiles);
        await db.files.bulkDelete(currentFiles.map((i) => i.path));
      }
      await refreshFileExplorer();
      onSubmit?.(data.path);
    } catch (err) {
      form.setError("path", { message: "Path already exists." });
    }
  }

  return (
    <Form {...form}>
      <form
        onSubmit={form.handleSubmit(_onSubmit)}
        className="w-full space-y-6"
      >
        <FormField
          control={form.control}
          name="path"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Path</FormLabel>
              <FormControl>
                <Input className="w-full" placeholder="path" {...field} />
              </FormControl>
              <FormDescription>
                This is the new path of your {type}.
              </FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />
        <Button variant="ghost" className="w-full bg-white text-black" type="submit" disabled={form.formState.isSubmitting}>
          {form.formState.isSubmitting ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Please wait
            </>
          ) : (
            "Submit"
          )}
        </Button>
      </form>
    </Form>
  );
}
