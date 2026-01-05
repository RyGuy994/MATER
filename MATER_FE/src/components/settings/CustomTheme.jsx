// filepath: MATER/MATER_FE/src/components/settings/CustomTheme.jsx
import { useEffect, useState } from "react";
import "./CustomTheme.css";

const CUSTOM_THEME_KEY = "mater_custom_theme";

// Default custom colors
const DEFAULT_CUSTOM_COLORS = {
  primary: "#208085",        // Teal
  secondary: "#5e5240",      // Brown
  background: "#fcfcf9",     // Cream
  surface: "#ffffff",        // White
  text: "#134252",           // Dark blue
  textSecondary: "#626c71",  // Gray
  success: "#208085",        // Teal
  error: "#c0152f",          // Red
  warning: "#a84b2f",        // Orange
};

export default function CustomTheme({ isActive }) {
  const [colors, setColors] = useState(DEFAULT_CUSTOM_COLORS);
  const [showPicker, setShowPicker] = useState(false);

  // Load custom colors on mount
  useEffect(() => {
    const saved = localStorage.getItem(CUSTOM_THEME_KEY);
    if (saved) {
      try {
        setColors(JSON.parse(saved));
      } catch (e) {
        console.error("Failed to parse custom theme:", e);
      }
    }
  }, []);

  // Apply colors to DOM when they change or theme becomes active
  useEffect(() => {
    if (!isActive) return;

    const root = document.documentElement;
    Object.entries(colors).forEach(([key, value]) => {
      root.style.setProperty(`--custom-${key}`, value);
    });

    // Save to localStorage
    localStorage.setItem(CUSTOM_THEME_KEY, JSON.stringify(colors));
  }, [colors, isActive]);

  const handleColorChange = (colorKey, newColor) => {
    setColors((prev) => ({
      ...prev,
      [colorKey]: newColor,
    }));
  };

  const handleReset = () => {
    setColors(DEFAULT_CUSTOM_COLORS);
    localStorage.removeItem(CUSTOM_THEME_KEY);
  };

  if (!isActive) {
    return null;
  }

  const colorGroups = [
    {
      label: "Core Colors",
      colors: ["primary", "secondary"],
    },
    {
      label: "Background & Text",
      colors: ["background", "surface", "text", "textSecondary"],
    },
    {
      label: "Status Colors",
      colors: ["success", "error", "warning"],
    },
  ];

  return (
    <div className="custom-theme-section">
      <button
        type="button"
        className="custom-theme-toggle"
        onClick={() => setShowPicker(!showPicker)}
      >
        {showPicker ? "Hide Color Picker" : "Show Color Picker"}
      </button>

      {showPicker && (
        <div className="custom-theme-picker">
          <p className="custom-theme-info">
            Customize your theme by selecting colors for different UI elements.
          </p>

          {colorGroups.map((group) => (
            <div key={group.label} className="color-group">
              <h4 className="color-group-label">{group.label}</h4>
              <div className="color-grid">
                {group.colors.map((colorKey) => (
                  <div key={colorKey} className="color-input-wrapper">
                    <label htmlFor={`color-${colorKey}`} className="color-label">
                      {colorKey.replace(/([A-Z])/g, " $1").trim()}
                    </label>
                    <div className="color-input-group">
                      <input
                        id={`color-${colorKey}`}
                        type="color"
                        value={colors[colorKey]}
                        onChange={(e) =>
                          handleColorChange(colorKey, e.target.value)
                        }
                        className="color-input"
                      />
                      <input
                        type="text"
                        value={colors[colorKey]}
                        onChange={(e) =>
                          handleColorChange(colorKey, e.target.value)
                        }
                        className="color-hex"
                        maxLength="7"
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}

          <div className="custom-theme-preview">
            <h4>Preview</h4>
            <div className="preview-grid">
              <div
                className="preview-box"
                style={{ backgroundColor: colors.background }}
              >
                <p style={{ color: colors.text }}>Text on Background</p>
              </div>
              <div
                className="preview-box"
                style={{ backgroundColor: colors.surface }}
              >
                <p style={{ color: colors.text }}>Text on Surface</p>
              </div>
              <button
                className="preview-btn"
                style={{ backgroundColor: colors.primary, color: "#fff" }}
              >
                Primary Button
              </button>
              <button
                className="preview-btn"
                style={{ backgroundColor: colors.success, color: "#fff" }}
              >
                Success
              </button>
              <button
                className="preview-btn"
                style={{ backgroundColor: colors.error, color: "#fff" }}
              >
                Error
              </button>
              <button
                className="preview-btn"
                style={{ backgroundColor: colors.warning, color: "#fff" }}
              >
                Warning
              </button>
            </div>
          </div>

          <button
            type="button"
            className="reset-colors-btn"
            onClick={handleReset}
          >
            Reset to Defaults
          </button>
        </div>
      )}
    </div>
  );
}
