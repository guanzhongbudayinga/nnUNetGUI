import os
import json
import shutil
import numpy as np
from PIL import Image
from skimage import io
import tifffile as tiff
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QLineEdit, QPushButton, QLabel, QVBoxLayout, QWidget, QFormLayout, QDialog, QGridLayout, QComboBox,QMessageBox, QListWidget, QInputDialog
)


def cut_tiff_into_parts(input_file_path, x_cuts, y_cuts):
    """
    Splits a TIFF file into equally sized parts and saves them into a directory.

    Args:
        input_file_path (str): Path to the TIFF file.
        x_cuts (int): Number of cuts along the x-axis.
        y_cuts (int): Number of cuts along the y-axis.

    Raises:
        ValueError: If the image dimensions are not divisible by the specified cuts.
    """
    # Open the TIFF file
    try:
        tiff_image = Image.open(input_file_path)
    except FileNotFoundError:
        raise FileNotFoundError("The specified TIFF file was not found.")

    if not tiff_image.is_animated:
        raise ValueError("The input image does not appear to be a stack.")

    # Get original dimensions
    width, height = tiff_image.size
    num_frames = tiff_image.n_frames

    # Calculate sub-region dimensions
    sub_width = width // (x_cuts + 1)
    sub_height = height // (y_cuts + 1)

    # Validate divisibility
    if width % (x_cuts + 1) != 0 or height % (y_cuts + 1) != 0:
        raise ValueError("Image dimensions are not perfectly divisible by the chosen cuts.")

    # Create the output directory
    base_name = os.path.splitext(os.path.basename(input_file_path))[0]
    save_dir = os.path.join(os.path.dirname(input_file_path), base_name)
    os.makedirs(save_dir, exist_ok=True)

    # Cut and save parts
    part_counter = 1
    for i in range(x_cuts + 1):
        for j in range(y_cuts + 1):
            x_start = i * sub_width
            y_start = j * sub_height
            # Create a stack for the cropped region
            cropped_stack = []
            for frame in range(num_frames):
                tiff_image.seek(frame)
                frame_data = np.array(tiff_image.crop((x_start, y_start, x_start + sub_width, y_start + sub_height)))
                cropped_stack.append(Image.fromarray(frame_data))
            # Save cropped stack as a new TIFF
            part_name = f"{base_name}_x{i}_y{j}.tif"
            part_path = os.path.join(save_dir, part_name)
            cropped_stack[0].save(part_path, save_all=True, append_images=cropped_stack[1:])
            part_counter += 1

    print(f"Processing complete. Files saved in: {save_dir}")

class NNUnetGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        print("Initializing GUI...")
        self.setWindowTitle("nnUNet Folder Setup")
        self.setGeometry(100, 100, 600, 600)

        # Main widget and layout
        self.central_widget = QWidget()
        self.layout = QVBoxLayout()

        # Dataset ID Input for Folder Creation
        self.label_dataset_id = QLabel("Enter Dataset ID (e.g., 001):")
        self.input_dataset_id = QLineEdit()
        self.layout.addWidget(self.label_dataset_id)
        self.layout.addWidget(self.input_dataset_id)

        # Dataset Name Input
        self.label_dataset = QLabel("Enter Dataset Name:")
        self.input_dataset = QLineEdit()
        self.layout.addWidget(self.label_dataset)
        self.layout.addWidget(self.input_dataset)

        # Folder Selection
        self.label_folder = QLabel("Select Input Folder:")
        self.btn_select_folder = QPushButton("Browse")
        self.btn_select_folder.clicked.connect(self.select_folder)
        self.input_folder = QLineEdit()
        self.input_folder.setReadOnly(True)
        self.layout.addWidget(self.label_folder)
        self.layout.addWidget(self.input_folder)
        self.layout.addWidget(self.btn_select_folder)

        # Create Folder Button
        self.btn_run = QPushButton("Create Folder Structure")
        self.btn_run.clicked.connect(self.run_processing)
        self.layout.addWidget(self.btn_run)

        # Generate Dataset.json Button
        self.btn_dataset_json = QPushButton("Generate Dataset.json")
        self.btn_dataset_json.clicked.connect(self.generate_dataset_json_dialog)
        self.layout.addWidget(self.btn_dataset_json)

        # nnUNet Plan and Preprocess Input and Button
        self.label_plan_preprocess = QLabel("Enter Dataset IDs for nnUNetv2 Plan and Preprocess (e.g., 1 2 3):")
        self.input_plan_preprocess = QLineEdit()
        self.layout.addWidget(self.label_plan_preprocess)
        self.layout.addWidget(self.input_plan_preprocess)

        self.btn_plan_preprocess = QPushButton("Run nnUNetv2 Plan and Preprocess")
        self.btn_plan_preprocess.clicked.connect(self.run_nnunet_plan_preprocess)
        self.layout.addWidget(self.btn_plan_preprocess)

        # Change TIF File Values Button
        self.btn_change_color = QPushButton("Change TIF File Colors in Folder")
        self.btn_change_color.clicked.connect(self.change_tif_colors_folder)
        self.layout.addWidget(self.btn_change_color)


        # Cut TIF Stack Button
        self.btn_cut_tif_stack = QPushButton("Cut TIF Stack (X/Y)")
        self.btn_cut_tif_stack.clicked.connect(self.cut_tif_file)
        self.layout.addWidget(self.btn_cut_tif_stack)


         # Add Combine Labels Button
        self.btn_combine_labels = QPushButton("Combine Labels")
        self.btn_combine_labels.clicked.connect(self.combine_labels)
        self.layout.addWidget(self.btn_combine_labels)

        # Add Create Substacks Button
        self.btn_create_substacks = QPushButton("Create Substacks")
        self.btn_create_substacks.clicked.connect(self.create_substacks)
        self.layout.addWidget(self.btn_create_substacks)
        
        # Set layout
        self.central_widget.setLayout(self.layout)
        self.setCentralWidget(self.central_widget)

        # Instance variables
        self.input_folder_path = ""
        self.dataset_id = ""
        self.dataset_name = ""

        print("GUI initialized.")

    def select_folder(self):
        """Open a file dialog to select the input folder."""
        print("Opening folder selection dialog...")  # Debug print
        folder = QFileDialog.getExistingDirectory(self, "Select Input Folder")
        if folder:
            self.input_folder_path = folder
            self.input_folder.setText(folder)
            print(f"Selected folder: {folder}")

    def validate_dataset_id(self):
        """Validate the Dataset ID input for folder creation."""
        dataset_id = self.input_dataset_id.text().strip()
        if not dataset_id.isdigit() or len(dataset_id) != 3:
            QMessageBox.warning(
                self,
                "Invalid Dataset ID",
                "Dataset ID must be a 3-digit number (e.g., 001)."
            )
            return None
        return dataset_id

    def validate_plan_preprocess_ids(self):
        """Validate the Dataset IDs for nnUNetv2 Plan and Preprocess."""
        ids = self.input_plan_preprocess.text().strip()
        if not ids:
            QMessageBox.warning(
                self,
                "Invalid Dataset IDs",
                "Please enter one or more Dataset IDs separated by spaces (e.g., 1 2 3)."
            )
            return None

        # Validate that all inputs are numbers
        id_list = ids.split()
        if not all(id.isdigit() for id in id_list):
            QMessageBox.warning(
                self,
                "Invalid Dataset IDs",
                "All Dataset IDs must be numbers (e.g., 1 2 3)."
            )
            return None

        return id_list

    def run_processing(self):
        """Run the processing logic."""
        print("Starting folder creation...")
        self.dataset_id = self.validate_dataset_id()
        if not self.dataset_id:
            return

        self.dataset_name = self.input_dataset.text()
        if not self.dataset_name:
            QMessageBox.warning(self, "Invalid Input", "Please enter a dataset name!")
            return
        if not self.input_folder_path:
            QMessageBox.warning(self, "Invalid Input", "Please select an input folder!")
            return

        try:
            print(f"Creating folder structure for dataset {self.dataset_id}_{self.dataset_name}...")  # Debug print
            self.create_folder_structure(self.input_folder_path, self.validate_dataset_id, self.dataset_name)
            QMessageBox.information(self, "Success", "Folder structure created successfully!")
            print("Folder structure created successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error occurred: {str(e)}")
            print(f"Exception occurred: {str(e)}")

    def create_folder_structure(self, input_folder, dataset_id, dataset_name):
        """Create the nnUNet folder structure."""
        print("Starting folder creation...")  # Debug print
        # Destination folder
        base_path = f"Z:/zhonghui-wen/nnUNet_raw/Dataset{self.dataset_id}_{self.dataset_name}"
        imagesTr_path = os.path.join(base_path, "imagesTr")
        imagesTs_path = os.path.join(base_path, "imagesTs")
        labelsTr_path = os.path.join(base_path, "labelsTr")

        # Create directories
        os.makedirs(imagesTr_path, exist_ok=True)
        os.makedirs(imagesTs_path, exist_ok=True)
        os.makedirs(labelsTr_path, exist_ok=True)
        print(f"Directories created at: {base_path}")  # Debug print

        # Copy files and generate JSON
        for root, dirs, files in os.walk(input_folder):
            for file in files:
                if file.endswith(".tif"):
                    src_file = os.path.join(root, file)
                    rel_dir = os.path.relpath(root, input_folder)
                    print(f"Processing file: {src_file} in {rel_dir}")  # Debug print

                    if rel_dir == "imagesTr":
                        dest_file = os.path.join(imagesTr_path, file.replace(".tif", "_0000.tif"))
                        shutil.copy(src_file, dest_file)
                        self.create_json(os.path.join(imagesTr_path, file))

                    elif rel_dir == "imagesTs":
                        dest_file = os.path.join(imagesTs_path, file.replace(".tif", "_0000.tif"))
                        shutil.copy(src_file, dest_file)
                        self.create_json(os.path.join(imagesTs_path, file))

                    elif rel_dir == "labelsTr":
                        dest_file = os.path.join(labelsTr_path, file)
                        shutil.copy(src_file, dest_file)
                        self.create_json(dest_file)

    def create_json(self, file_path):
        """Generate a JSON file with spacing metadata."""
        json_content = {"spacing": [1, 1, 1]}
        json_file_path = file_path.replace(".tif", ".json")
        print(f"Creating JSON file: {json_file_path}")  # Debug print
        with open(json_file_path, "w") as json_file:
            json.dump(json_content, json_file, indent=4)

    def generate_dataset_json_dialog(self):
        """Open a dialog to input label names and generate dataset.json."""
        print("Starting dataset.json generation...")
        labels = self.analyze_labels()
        if not labels:
            QMessageBox.warning(self, "Error", "No labels found in labelsTr folder!")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Generate Dataset.json")
        layout = QGridLayout()

        # Ensure background (0) is added automatically
        label_widgets = {}
        for idx, label_value in enumerate(sorted(labels)):
            label_name = "background" if label_value == 0 else ""
            layout.addWidget(QLabel(f"Label {label_value}:"), idx, 0)
            input_field = QLineEdit(label_name)
            input_field.setReadOnly(label_value == 0)  # Background is predefined
            layout.addWidget(input_field, idx, 1)
            label_widgets[label_value] = input_field

        btn_generate = QPushButton("Generate")
        layout.addWidget(btn_generate, len(labels), 0, 1, 2)

        def generate_dataset_json():
            print("Generating dataset.json...")
            label_dict = {}
            for label_value, widget in label_widgets.items():
                label_name = widget.text().strip()
                if label_name and label_name not in label_dict:
                    label_dict[label_name] = int(label_value)  # Ensure values are integers

            dataset_json_content = {
                "channel_names": {"0": "Tomo"},
                "labels": label_dict,
                "numTraining": len(os.listdir(os.path.join(self.input_folder_path, "imagesTr"))),
                "file_ending": ".tif",
            }

            base_path = f"Z:/zhonghui-wen/nnUNet_raw/Dataset{self.dataset_id}_{self.dataset_name}"
            json_path = os.path.join(base_path, "dataset.json")
            with open(json_path, "w") as json_file:
                json.dump(dataset_json_content, json_file, indent=4)

            print(f"dataset.json created at {json_path}")
            dialog.accept()

        btn_generate.clicked.connect(generate_dataset_json)
        dialog.setLayout(layout)
        dialog.exec_()

    def analyze_labels(self):
        """Analyze labels from a random labelsTr file."""
        labels_tr_path = os.path.join(self.input_folder_path, "labelsTr")
        if not os.path.exists(labels_tr_path):
            return None

        label_files = [f for f in os.listdir(labels_tr_path) if f.endswith(".tif")]
        if not label_files:
            return None

        random_file = os.path.join(labels_tr_path, label_files[0])
        try:
            with Image.open(random_file) as img:
                label_values = np.unique(np.array(img))
                return list(map(int, label_values))  # Convert to standard Python int
        except Exception as e:
            print(f"Error reading label file: {e}")
            return None

    def create_json(self, file_path):
        """Generate a JSON file with spacing metadata."""
        json_content = {"spacing": [1, 1, 1]}
        json_file_path = file_path.replace(".tif", ".json")
        with open(json_file_path, "w") as json_file:
            json.dump(json_content, json_file, indent=4)

    def run_nnunet_plan_preprocess(self):
        """Run the nnUNetv2 planning and preprocessing command."""
        dataset_ids = self.validate_plan_preprocess_ids()
        if not dataset_ids:
            return

        command = f"nnUNetv2_plan_and_preprocess -d {' '.join(dataset_ids)} --verify_dataset_integrity"
        print(f"Executing command: {command}")
        os.system(command)  # Execute command in the console

    def change_tif_colors_folder(self):
        """Change color values for all TIF files in a folder."""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder Containing TIF Files")
        if not folder:
            QMessageBox.warning(self, "No Folder Selected", "Please select a folder.")
            return

        # Detect all unique values in the folder
        try:
            unique_values = self.get_unique_values_in_folder(folder)
            if not unique_values:
                QMessageBox.warning(self, "No Data", "No valid TIF files found in the folder.")
                return
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error reading TIF files: {e}")
            return

        # Pop-up window to select values
        dialog = QDialog(self)
        dialog.setWindowTitle("Change TIF File Colors")
        layout = QGridLayout()

        layout.addWidget(QLabel("Select Value to Change:"), 0, 0)
        dropdown_old_value = QComboBox()
        dropdown_old_value.addItems([str(v) for v in unique_values])
        layout.addWidget(dropdown_old_value, 0, 1)

        layout.addWidget(QLabel("Enter New Value:"), 1, 0)
        input_new_value = QLineEdit()
        layout.addWidget(input_new_value, 1, 1)

        btn_process = QPushButton("Process")
        layout.addWidget(btn_process, 2, 0, 1, 2)

        dialog.setLayout(layout)

        def process_color_change():
            # Validate new value input
            try:
                old_value = int(dropdown_old_value.currentText())
                new_value = int(input_new_value.text())
            except ValueError:
                QMessageBox.warning(dialog, "Invalid Input", "Please enter a valid integer for the new value.")
                return

            # Perform the color change on all files in the folder
            try:
                for fname in os.listdir(folder):
                    filepath = os.path.join(folder, fname)
                    if os.path.isfile(filepath) and fname.endswith(".tif"):
                        print(f"Processing file: {fname}")
                        self.change_color_in_tif(filepath, old_value, new_value)
                QMessageBox.information(dialog, "Success", "Color values updated successfully.")
                dialog.accept()
            except Exception as e:
                QMessageBox.critical(dialog, "Error", f"Failed to process files: {e}")

        btn_process.clicked.connect(process_color_change)
        dialog.exec_()

    def get_unique_values_in_folder(self, folder):
        """Get unique pixel values across all TIF files in a folder."""
        unique_values = set()
        for fname in os.listdir(folder):
            filepath = os.path.join(folder, fname)
            if os.path.isfile(filepath) and fname.endswith(".tif"):
                with Image.open(filepath) as img:
                    for i in range(img.n_frames):
                        img.seek(i)
                        frame_data = np.array(img)
                        unique_values.update(np.unique(frame_data))
        return sorted(unique_values)

    def change_color_in_tif(self, filepath, old_value, new_value):
        """Change a specific color value in all frames of a TIF file."""
        with Image.open(filepath) as img:
            frames = []
            for i in range(img.n_frames):
                img.seek(i)
                frame_data = np.array(img)
                frame_data[frame_data == old_value] = new_value
                frames.append(frame_data)

            # Save the updated file
            output_file = filepath  # Overwrite the original file
            io.imsave(output_file, np.stack(frames).astype(np.uint8))




    def cut_tif_file(self):
        """Cut a TIF stack into smaller pieces based on nnUNet-style user input."""
        file, _ = QFileDialog.getOpenFileName(self, "Select TIF File", "", "TIF Files (*.tif)")
        if not file:
            QMessageBox.warning(self, "No File Selected", "Please select a TIF file.")
            return

        # Create dialog for user input
        dialog = QDialog(self)
        dialog.setWindowTitle("Cut TIF Stack")
        layout = QGridLayout()

        layout.addWidget(QLabel("Enter divisions for x and y axes (e.g., 2x2 for 1 cut per axis):"), 0, 0, 1, 2)

        layout.addWidget(QLabel("X Divisions:"), 1, 0)
        input_x = QLineEdit()
        layout.addWidget(input_x, 1, 1)

        layout.addWidget(QLabel("Y Divisions:"), 2, 0)
        input_y = QLineEdit()
        layout.addWidget(input_y, 2, 1)

        btn_process = QPushButton("Process")
        layout.addWidget(btn_process, 3, 0, 1, 2)

        dialog.setLayout(layout)

        def process_cut():
            try:
                x_divisions = int(input_x.text()) if input_x.text() else 1
                y_divisions = int(input_y.text()) if input_y.text() else 1
            except ValueError:
                QMessageBox.warning(dialog, "Invalid Input", "Please enter valid integers for divisions.")
                return

            if x_divisions <= 0 or y_divisions <= 0:
                QMessageBox.warning(dialog, "Invalid Input", "Division numbers must be positive integers.")
                return

            x_cuts = x_divisions - 1
            y_cuts = y_divisions - 1

            try:
                cut_tiff_into_parts(file, x_cuts, y_cuts)
                QMessageBox.information(dialog, "Success", "TIF file successfully cut into parts.")
                dialog.accept()
            except ValueError as ve:
                QMessageBox.warning(dialog, "Invalid Cuts", str(ve))
            except Exception as e:
                QMessageBox.critical(dialog, "Error", f"Failed to cut TIF file: {e}")

        btn_process.clicked.connect(process_cut)
        dialog.exec_()
    def combine_labels(self):
        """Combine multiple TIFF files into a single labeled TIFF."""
        files, _ = QFileDialog.getOpenFileNames(self, "Select TIFF Files", "", "TIFF Files (*.tif)")
        if not files:
            QMessageBox.warning(self, "No Files Selected", "Please select at least two TIFF files.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Assign Labels to Files")
        layout = QGridLayout()

        labels = {}
        for idx, file in enumerate(files):
            layout.addWidget(QLabel(f"File {idx + 1}: {os.path.basename(file)}"), idx, 0)
            label_input = QLineEdit()
            layout.addWidget(label_input, idx, 1)
            labels[file] = label_input

        btn_process = QPushButton("Combine")
        layout.addWidget(btn_process, len(files), 0, 1, 2)
        dialog.setLayout(layout)

        def process_combine():
            try:
                combined = None
                for file, label_input in labels.items():
                    label_value = int(label_input.text())
                    data = tiff.imread(file)
                    if combined is None:
                        combined = np.zeros_like(data, dtype=np.uint8)

                    combined[data == 255] = label_value

                output_file = QFileDialog.getSaveFileName(self, "Save Combined TIFF", "", "TIFF Files (*.tif)")[0]
                if not output_file:
                    return

                tiff.imwrite(output_file, combined)
                QMessageBox.information(dialog, "Success", f"Combined TIFF saved at {output_file}")
                print(f"Combined TIFF saved at {output_file}")
                dialog.accept()
            except ValueError:
                QMessageBox.warning(dialog, "Invalid Input", "Please enter valid integers for all labels.")
            except Exception as e:
                QMessageBox.critical(dialog, "Error", f"Failed to combine labels: {e}")

        btn_process.clicked.connect(process_combine)
        dialog.exec_()

    def create_substacks(self):
        """Create substacks from a TIFF file."""
        file, _ = QFileDialog.getOpenFileName(self, "Select TIFF File", "", "TIFF Files (*.tif)")
        if not file:
            QMessageBox.warning(self, "No File Selected", "Please select a TIFF file.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Create Substacks")
        layout = QGridLayout()

        layout.addWidget(QLabel("Start Frame:"), 0, 0)
        input_start = QLineEdit()
        layout.addWidget(input_start, 0, 1)

        layout.addWidget(QLabel("End Frame:"), 1, 0)
        input_end = QLineEdit()
        layout.addWidget(input_end, 1, 1)

        layout.addWidget(QLabel("Substack Size:"), 2, 0)
        input_size = QLineEdit()
        layout.addWidget(input_size, 2, 1)

        btn_process = QPushButton("Generate Substacks")
        layout.addWidget(btn_process, 3, 0, 1, 2)
        dialog.setLayout(layout)

        def process_substacks():
            try:
                start_frame = int(input_start.text())
                end_frame = int(input_end.text())
                substack_size = int(input_size.text())

                output_dir = QFileDialog.getExistingDirectory(self, "Select Output Directory")
                if not output_dir:
                    return

                with tiff.TiffFile(file) as tif:
                    frames = tif.asarray()

                if start_frame < 0 or end_frame >= frames.shape[0]:
                    raise ValueError("Start or end frame is out of bounds.")

                frames_to_process = frames[start_frame:end_frame + 1]

                substack_count = 0
                for i in range(0, len(frames_to_process), substack_size):
                    substack = frames_to_process[i:i + substack_size]
                    if len(substack) == substack_size:
                        substack_start = start_frame + i
                        substack_end = substack_start + substack_size - 1
                        output_path = os.path.join(output_dir, f"substack_{substack_start}_{substack_end}.tif")
                        tiff.imwrite(output_path, substack)
                        substack_count += 1

                QMessageBox.information(dialog, "Success", f"Successfully created {substack_count} substacks.")
                print(f"Successfully created {substack_count} substacks in '{output_dir}'.")
                dialog.accept()
            except ValueError as ve:
                QMessageBox.warning(dialog, "Invalid Input", str(ve))
            except Exception as e:
                QMessageBox.critical(dialog, "Error", f"Failed to create substacks: {e}")

        btn_process.clicked.connect(process_substacks)
        dialog.exec_()

# Run the application
if __name__ == "__main__":
    app = QApplication([])
    window = NNUnetGUI()
    window.show()
    app.exec_()
