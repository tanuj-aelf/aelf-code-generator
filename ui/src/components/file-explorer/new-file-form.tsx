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
import { Input } from "@/components/ui/input";
import { Loader2 } from "lucide-react";
import { useRefreshFileExplorer } from "./FileExplorer";
import { usePathname } from "next/navigation";
import { db } from "@/data/db";

const FormSchema = z.object({
  path: z.string(),
});

export function NewFileForm({
  defaultPath,
  onSubmit,
}: {
  defaultPath?: string;
  onSubmit?: (path: string) => void;
}) {
  const pathname = usePathname().replace("/", "");
  const refreshFileExplorer = useRefreshFileExplorer();

  const form = useForm<z.infer<typeof FormSchema>>({
    resolver: zodResolver(FormSchema),
    defaultValues: {
      path: defaultPath,
    },
  });

  async function _onSubmit(data: z.infer<typeof FormSchema>) {
    form.clearErrors();
    try {
      await db.files.add({
        path: `/workspace/${pathname}/${data.path}`,
        contents: "",
      });
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
                <Input className="w-full" placeholder="file path" {...field} />
              </FormControl>
              <FormDescription>
                This is the path of your new file.
              </FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />
        <Button
          variant="ghost"
          className="w-full bg-white text-black"
          type="submit"
          disabled={form.formState.isSubmitting}
        >
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
