#!/usr/bin/env python3
"""Minimalist GUI for Audio Metadata Completionist."""

import asyncio
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Optional

from src import __version__
from src.config import settings
from src.core.file_processor import FileProcessor
from src.pipeline.enrichment_pipeline import EnrichmentPipeline
from src.utils.logging_config import setup_logging


class AudioMetadataGUI:
    """Minimalist GUI for audio metadata enrichment."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(f"Audio Metadata Completionist v{__version__}")
        self.root.geometry("600x400")
        self.root.resizable(False, False)

        # Set theme colors
        self.bg_color = "#2b2b2b"
        self.fg_color = "#ffffff"
        self.button_color = "#404040"
        self.accent_color = "#4a9eff"

        self.root.configure(bg=self.bg_color)

        self.selected_path: Optional[Path] = None
        self.is_processing = False

        self._setup_ui()
        self._check_api_key()

    def _setup_ui(self):
        """Setup the user interface."""
        # Main container
        main_frame = tk.Frame(self.root, bg=self.bg_color, padx=30, pady=30)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = tk.Label(
            main_frame,
            text="Audio Metadata Completionist",
            font=("Arial", 16, "bold"),
            bg=self.bg_color,
            fg=self.accent_color,
        )
        title_label.pack(pady=(0, 20))

        # Path selection frame
        path_frame = tk.Frame(main_frame, bg=self.bg_color)
        path_frame.pack(fill=tk.X, pady=(0, 20))

        self.path_label = tk.Label(
            path_frame,
            text="No folder selected",
            font=("Arial", 10),
            bg=self.button_color,
            fg=self.fg_color,
            relief=tk.SUNKEN,
            anchor=tk.W,
            padx=10,
            pady=8,
        )
        self.path_label.pack(fill=tk.X, pady=(0, 10))

        select_button = tk.Button(
            path_frame,
            text="Select Folder",
            command=self._select_folder,
            font=("Arial", 10),
            bg=self.accent_color,
            fg=self.fg_color,
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor="hand2",
        )
        select_button.pack()

        # Options frame
        options_frame = tk.LabelFrame(
            main_frame,
            text="Options",
            font=("Arial", 10, "bold"),
            bg=self.bg_color,
            fg=self.fg_color,
            padx=15,
            pady=10,
        )
        options_frame.pack(fill=tk.X, pady=(0, 20))

        # Checkboxes
        self.recursive_var = tk.BooleanVar(value=True)
        self.skip_existing_var = tk.BooleanVar(value=False)
        self.force_artwork_var = tk.BooleanVar(value=False)
        self.dry_run_var = tk.BooleanVar(value=False)

        tk.Checkbutton(
            options_frame,
            text="Recursive search",
            variable=self.recursive_var,
            bg=self.bg_color,
            fg=self.fg_color,
            selectcolor=self.button_color,
            font=("Arial", 9),
        ).pack(anchor=tk.W, pady=2)

        tk.Checkbutton(
            options_frame,
            text="Skip files with existing metadata",
            variable=self.skip_existing_var,
            bg=self.bg_color,
            fg=self.fg_color,
            selectcolor=self.button_color,
            font=("Arial", 9),
        ).pack(anchor=tk.W, pady=2)

        tk.Checkbutton(
            options_frame,
            text="Force artwork download",
            variable=self.force_artwork_var,
            bg=self.bg_color,
            fg=self.fg_color,
            selectcolor=self.button_color,
            font=("Arial", 9),
        ).pack(anchor=tk.W, pady=2)

        tk.Checkbutton(
            options_frame,
            text="Dry run (preview only)",
            variable=self.dry_run_var,
            bg=self.bg_color,
            fg=self.fg_color,
            selectcolor=self.button_color,
            font=("Arial", 9),
        ).pack(anchor=tk.W, pady=2)

        # Start button
        self.start_button = tk.Button(
            main_frame,
            text="Start Processing",
            command=self._start_processing,
            font=("Arial", 12, "bold"),
            bg=self.accent_color,
            fg=self.fg_color,
            relief=tk.FLAT,
            padx=40,
            pady=12,
            cursor="hand2",
        )
        self.start_button.pack(pady=(0, 15))

        # Status label
        self.status_label = tk.Label(
            main_frame,
            text="Ready",
            font=("Arial", 10),
            bg=self.bg_color,
            fg=self.fg_color,
        )
        self.status_label.pack()

    def _check_api_key(self):
        """Check if AcousticID API key is configured."""
        if not settings.acoustid_api_key:
            messagebox.showerror(
                "Configuration Error",
                "AcousticID API key not configured.\n\n"
                "Please set ACOUSTID_API_KEY in your .env file.\n"
                "Get your API key from: https://acoustid.org/api-key",
            )

    def _select_folder(self):
        """Open folder selection dialog."""
        folder = filedialog.askdirectory(title="Select Audio Folder")
        if folder:
            self.selected_path = Path(folder)
            # Truncate path if too long for display
            display_path = str(self.selected_path)
            if len(display_path) > 60:
                display_path = "..." + display_path[-57:]
            self.path_label.config(text=display_path)

    def _start_processing(self):
        """Start the enrichment process."""
        if not self.selected_path:
            messagebox.showwarning("No Folder Selected", "Please select a folder first.")
            return

        if not settings.acoustid_api_key:
            messagebox.showerror(
                "Configuration Error",
                "AcousticID API key not configured.\n\n"
                "Please set ACOUSTID_API_KEY in your .env file.",
            )
            return

        if self.is_processing:
            return

        self.is_processing = True
        self.start_button.config(state=tk.DISABLED, bg=self.button_color)
        self.status_label.config(text="Processing...", fg="#ffaa00")

        # Run enrichment in background
        self.root.after(100, self._run_enrichment)

    def _run_enrichment(self):
        """Run the enrichment process."""
        try:
            setup_logging()

            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Run async enrichment
            loop.run_until_complete(self._enrich_async())
            loop.close()

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred:\n\n{str(e)}")
            self.status_label.config(text="Error", fg="#ff4444")
        finally:
            self.is_processing = False
            self.start_button.config(state=tk.NORMAL, bg=self.accent_color)

    async def _enrich_async(self):
        """Async enrichment workflow."""
        pipeline = EnrichmentPipeline(dry_run=self.dry_run_var.get())

        # Find audio files
        self.status_label.config(text="Scanning for audio files...")
        self.root.update()

        audio_files = FileProcessor.find_audio_files(
            self.selected_path,
            recursive=self.recursive_var.get()
        )

        if not audio_files:
            messagebox.showinfo("No Files Found", "No audio files found in the selected folder.")
            self.status_label.config(text="Ready", fg=self.fg_color)
            return

        self.status_label.config(text=f"Found {len(audio_files)} file(s). Processing...")
        self.root.update()

        # Enrich files
        results, stats = await pipeline.enrich_files(
            audio_files,
            skip_existing=self.skip_existing_var.get(),
            force_artwork=self.force_artwork_var.get(),
            max_concurrent=4,
        )

        # Show results
        success_rate = stats.success_rate()
        result_message = (
            f"Processing Complete!\n\n"
            f"Total files: {stats.total_files}\n"
            f"Successful: {stats.successful} ({success_rate:.1f}%)\n"
            f"Identified: {stats.identified}\n"
            f"Artwork added: {stats.artwork_added}\n"
            f"Failed: {stats.failed}"
        )

        if self.dry_run_var.get():
            result_message = "DRY RUN - No changes written\n\n" + result_message

        messagebox.showinfo("Results", result_message)
        self.status_label.config(text="Done!", fg="#44ff44")


def main():
    """Main entry point for GUI."""
    root = tk.Tk()
    app = AudioMetadataGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
