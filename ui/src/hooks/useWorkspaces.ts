import { db } from "@/data/db";
import useSWR from "swr";

export function useWorkspaces() {
  return useSWR("workspaces", async () => {
    return (await db.workspaces.toArray()).filter(
      (i) => !i.name.startsWith("/")
    );
  });
}
