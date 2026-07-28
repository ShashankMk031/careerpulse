import React from "react";

interface PageContainerProps {
  children: React.ReactNode;
}

export default function PageContainer({ children }: PageContainerProps) {
  return (
    <main
      className="flex-1 p-4 md:p-6 lg:p-8 max-w-7xl w-full mx-auto focus:outline-none"
      id="main-content"
      tabIndex={-1}
    >
      {children}
    </main>
  );
}
