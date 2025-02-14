"use client";

import { useEffect, useState } from "react";
import { db, Workspace } from "@/db/db"; // Ensure you have the db instance imported
import Link from "next/link";
import { Header } from "@/components/header";

export default function Workplace() {
  const [projects, setProjects] = useState<Workspace[]>([]);

  useEffect(() => {
    const fetchProjects = async () => {
      const allProjects = await db.workspaces.toArray(); // Fetch all projects from the database
      allProjects && setProjects(allProjects); // Directly set the state with the array of projects
    };

    fetchProjects();
  }, []);

  return (
    <div className="flex flex-col min-h-screen bg-gray-900 p-8 pt-[100px]">
      <Header />
      <h1 className="text-4xl font-extrabold text-blue-400 mb-6">
        Your Workspaces
      </h1>
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6 w-full max-w-6xl">
        {projects.map((project: Workspace) => (
          <Link
            key={project.name}
            href={`/${project.name}`}
            className="group relative p-6 rounded-xl shadow-lg cursor-pointer backdrop-blur-xl bg-opacity-20 border border-gray-700 transition-transform transform hover:scale-105 hover:border-blue-500"
          >
            {/* Background Glow Effect */}
            <div className="absolute inset-0 bg-gradient-to-br from-gray-800 to-gray-900 opacity-25 rounded-xl"></div>

            {/* Decorative Corner Glow */}
            <div className="absolute top-0 left-0 w-2 h-2 bg-blue-500 rounded-full shadow-lg group-hover:animate-ping"></div>
            <div className="absolute bottom-0 right-0 w-2 h-2 bg-purple-500 rounded-full shadow-lg group-hover:animate-ping"></div>

            {/* Content */}
            <h2 className="text-xl font-bold text-white relative z-10">
              {project.name}
            </h2>
            <p className="text-gray-400 text-sm mt-2 relative z-10">
              A brief description of {project.name}.
            </p>
          </Link>
        ))}
      </div>
    </div>
  );
}
