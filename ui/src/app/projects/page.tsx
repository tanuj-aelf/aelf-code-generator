"use client";

import { useEffect, useState } from "react";
import { db, Workspace } from "@/data/db"; // Ensure you have the db instance imported
import ProjectCard from "@/components/ui/project-card";
import { MainLayout } from "@/components/layout/MainLayout";

export default function Workplace() {
  const [projects, setProjects] = useState<Workspace[]>([]);

  const fetchProjects = async () => {
    const allProjects = await db.workspaces.toArray(); // Fetch all projects from the database
    allProjects && setProjects(allProjects); // Directly set the state with the array of projects
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  return (
    <MainLayout className="flex flex-col min-h-screen bg-gray-900 p-8 pt-[100px]">
      <div className="max-w-[1536px] w-full mx-auto">
        <h2 className="text-2xl text-white font-semibold mb-6">
          Your Workspaces
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6 w-full max-w-6xl">
          {projects.map((project: Workspace, index) => (
            <ProjectCard key={index} projectDetails={project} reloadProjects={fetchProjects}/>
          ))}
        </div>
      </div>
    </MainLayout>
  );
}
