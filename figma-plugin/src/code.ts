import { GenerateUIResponse, PluginMessage } from "./types";
import { renderAllScreens } from "./renderer";

figma.showUI(__html__, { width: 420, height: 520 });

figma.ui.onmessage = async (msg: PluginMessage) => {
  if (msg.type === "render") {
    try {
      const response = msg.payload as GenerateUIResponse;

      if (!response.success) {
        figma.ui.postMessage({
          type: "render-error",
          error: `API returned success=false. Errors: ${response.errors.join(", ")}`,
        });
        return;
      }

      if (response.screens.length === 0) {
        figma.ui.postMessage({
          type: "render-error",
          error: "No screens to render.",
        });
        return;
      }

      const frames = await renderAllScreens(response.screens);

      if (frames.length > 0) {
        figma.viewport.scrollAndZoomIntoView(frames);
      }

      figma.ui.postMessage({
        type: "render-complete",
        screenCount: frames.length,
      });

      figma.notify(`Rendered ${frames.length} screen(s) successfully.`);
    } catch (error) {
      const errorMsg =
        error instanceof Error ? error.message : String(error);
      console.error("[code.ts] Rendering failed:", errorMsg);

      figma.ui.postMessage({
        type: "render-error",
        error: errorMsg,
      });

      figma.notify(`Rendering failed: ${errorMsg}`, { error: true });
    }
  }
};
