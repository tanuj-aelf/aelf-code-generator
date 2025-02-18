import {
  ContextMenu,
  ContextMenuContent,
  ContextMenuItem,
  ContextMenuShortcut,
  ContextMenuTrigger,
} from "@/components/ui/context-menu";
import { Pencil, Delete, FilePlus, FolderPlus } from "lucide-react";
import React from "react";

export enum IAction {
  RENAME,
  DELETE,
  NEW_FILE,
  NEW_FOLDER,
}

interface IContextMenuProps extends React.PropsWithChildren {
  handleClick: (action: IAction) => void;
}

export function FileContextMenu({ children, handleClick }: IContextMenuProps) {
  return (
    <ContextMenu>
      <ContextMenuTrigger asChild>{children}</ContextMenuTrigger>
      <ContextMenuContent
        className="w-64"
        onClick={(e) => {
          e.stopPropagation();
        }}
      >
        <RenameItem onClick={() => handleClick(IAction.RENAME)} />
        <DeleteItem onClick={() => handleClick(IAction.DELETE)} />
      </ContextMenuContent>
    </ContextMenu>
  );
}

export function FolderContextMenu({
  children,
  handleClick,
}: IContextMenuProps) {
  return (
    <ContextMenu>
      <ContextMenuTrigger asChild>{children}</ContextMenuTrigger>
      <ContextMenuContent
        className="w-64"
        onClick={(e) => {
          e.stopPropagation();
        }}
      >
        <ContextMenuItem onClick={() => handleClick(IAction.NEW_FILE)}>
          <FilePlus className="w-4 h-4 mr-2" />
          <span>New File</span>
          {/* <ContextMenuShortcut>Ctrl+N</ContextMenuShortcut> */}
        </ContextMenuItem>
        {/* <ContextMenuItem onClick={() => handleClick(IAction.NEW_FOLDER)}>
          <FolderPlus className="w-4 h-4 mr-2" />
          <span>New Folder</span>
          <ContextMenuShortcut>Ctrl+Shift+N</ContextMenuShortcut>
        </ContextMenuItem> */}
        <RenameItem onClick={() => handleClick(IAction.RENAME)} />
        <DeleteItem onClick={() => handleClick(IAction.DELETE)} />
      </ContextMenuContent>
    </ContextMenu>
  );
}

interface IMenuItemProps {
  onClick: () => void;
}

const DeleteItem = ({ onClick }: IMenuItemProps) => (
  <ContextMenuItem onClick={onClick}>
    <Delete className="w-4 h-4 mr-2" />
    <span>Delete</span>
    {/* <ContextMenuShortcut>Del</ContextMenuShortcut> */}
  </ContextMenuItem>
);

const RenameItem = ({ onClick }: IMenuItemProps) => (
  <ContextMenuItem onClick={onClick}>
    <Pencil className="w-4 h-4 mr-2" />
    <span>Rename</span>
    {/* <ContextMenuShortcut>F2</ContextMenuShortcut> */}
  </ContextMenuItem>
);