import { GenerateUIResponse, PluginMessage } from "./types";
import { renderAllScreens } from "./renderer";
import {
  renderAllDesignScreens,
  GenerateDesignResponse,
} from "./figmaTreeRenderer";

figma.showUI(__html__, { width: 420, height: 520 });

figma.ui.onmessage = async (msg: PluginMessage) => {
  // v1 renderer (legacy component-based format)
  if (msg.type === "render") {
    try {
      const response = msg.payload as GenerateUIResponse;

      if (!response.success) {
        figma.ui.postMessage({
          type: "render-error",
          error: "API returned success=false. Errors: " + response.errors.join(", "),
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

      figma.notify("Rendered " + frames.length + " screen(s) successfully.");
    } catch (error) {
      var errorMsg =
        error instanceof Error ? error.message : String(error);
      console.error("[code.ts] Rendering failed:", errorMsg);

      figma.ui.postMessage({
        type: "render-error",
        error: errorMsg,
      });

      figma.notify("Rendering failed: " + errorMsg, { error: true });
    }
  }

  // v2 renderer (HTML-to-Figma tree format)
  if (msg.type === "render-design") {
    try {
      var response2 = msg.payload as unknown as GenerateDesignResponse;

      if (!response2.success) {
        figma.ui.postMessage({
          type: "render-error",
          error: "API returned success=false. Errors: " + response2.errors.join(", "),
        });
        return;
      }

      if (response2.screens.length === 0) {
        figma.ui.postMessage({
          type: "render-error",
          error: "No screens to render.",
        });
        return;
      }

      var frames2 = await renderAllDesignScreens(response2.screens);

      if (frames2.length > 0) {
        figma.viewport.scrollAndZoomIntoView(frames2);
      }

      figma.ui.postMessage({
        type: "render-complete",
        screenCount: frames2.length,
      });

      figma.notify("Rendered " + frames2.length + " design screen(s) successfully.");
    } catch (error) {
      var errorMsg2 =
        error instanceof Error ? error.message : String(error);
      console.error("[code.ts] Design rendering failed:", errorMsg2);

      figma.ui.postMessage({
        type: "render-error",
        error: errorMsg2,
      });

      figma.notify("Rendering failed: " + errorMsg2, { error: true });
    }
  }
};
