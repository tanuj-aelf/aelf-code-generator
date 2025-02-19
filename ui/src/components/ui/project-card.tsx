import React from "react";
import { Trash2, ExternalLink } from "lucide-react";
import { useRouter } from "next/navigation";

import { db, Workspace } from "@/data/db";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "./dropdown-menu";
import { Button } from "./button";
import { BurgetMenu } from "./icons";

const ProjectCard = ({
  projectDetails,
  reloadProjects,
}: {
  projectDetails: Workspace;
  reloadProjects: () => void;
}) => {
  const router = useRouter();

  const handleDeleteWorkspace = async () => {
    await db.files
      .filter((file) =>
        file.path.startsWith(`/workspace/${projectDetails.name}/`)
      )
      .delete();
    await db.workspaces.delete(projectDetails.name);
    reloadProjects();
  };
  return (
    <div
      key={projectDetails.name}
      className="group relative p-5 pr-10 rounded-xl shadow-lg cursor-pointer backdrop-blur-xl bg-opacity-20 border border-gray-700 transition-transform transform hover:border-blue-500"
    >
      <div className="flex right-2 top-4 absolute justify-end">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              className="text-gray-300 hover:text-white px-2"
            >
              <BurgetMenu />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent className="w-10">
            <DropdownMenuItem
              className="mb-1"
              onClick={() => router.push(`/${projectDetails.name}`)}
            >
              <ExternalLink className="h-4 w-4 mr-2" /> Open
            </DropdownMenuItem>
            <DropdownMenuItem
              className="text-red-500"
              onClick={handleDeleteWorkspace}
            >
              <Trash2 className="h-4 w-4 mr-2" /> Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
      <h2 className="text-md font-bold text-white relative z-10">
        {projectDetails.name}
      </h2>
    </div>
  );
};

export default ProjectCard;
