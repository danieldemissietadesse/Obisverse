// Import necessary dependencies
import React from 'react';

// Define the Layout component
const Layout: React.FC = ({ children }) => {
  return (
    <div className="min-h-screen flex flex-col">
      {/* Header section can be added here if needed */}
      <main>{children}</main>
      {/* Footer section can be added here if needed */}
    </div>
  );
};

export default Layout;
