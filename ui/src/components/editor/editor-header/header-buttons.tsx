import { Button } from "@/components/ui/button";
import React, { ReactNode } from "react";

interface IProps {
  title: string;
  disabled: boolean;
  onClick: () => void;
  icon: ReactNode;
}

const HeadeButtons = ({ headerButtons }: { headerButtons: IProps[] }) => {
  return headerButtons.map((data, index) => (
    <Button
      key={index}
      variant="ghost"
      className="text-[0px] xl:text-[12px] 2xl:text-[14px] px-3 xl:px-2 2xl:px-4 text-gray-400 hover:text-white"
      onClick={data.onClick}
      disabled={data.disabled}
    >
      {data.icon} {data.title}
    </Button>
  ));
};

export default HeadeButtons;
