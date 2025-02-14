import { db } from "@/db/db";
import useSWR from "swr";

export function useWorkspaces() {
  return useSWR("workspaces", async () => {
    return (await db.workspaces.toArray()).filter(
      (i) => !i.name.startsWith("/")
    );
  });
}
