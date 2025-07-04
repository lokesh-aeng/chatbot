import { useEffect, useState } from "react";
import "./ThemeToggleButton.css"
import light from "/src/images/light.png"
import dark from "/src/images/dark.png"

function ThemeToggleButton() {
  const [theme, setTheme] = useState(() => {
    // Initialize from localStorage if available
    return localStorage.getItem("theme") || "light";
  });

  useEffect(() => {
    document.body.className = theme;
    localStorage.setItem("theme", theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => (prev === "light" ? "dark" : "light"));
  };

  return (
    <button className="theme-toggle" onClick={toggleTheme} title={theme==="light"? "dark mode" : "light mode"}>
      <img 
        src={theme==="light"? dark : light} 
        alt="Theme Toggle"
        className="theme-icon"
      />
    </button>
  );
}

export default ThemeToggleButton;