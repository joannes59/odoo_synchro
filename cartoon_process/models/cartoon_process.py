from odoo import models, fields
import psutil
import subprocess

class CartoonProcess(models.Model):
    """
    Model to manage and track Python scripts and their processes.
    """
    _name = 'cartoon.process'  # Technical name of the model
    _description = 'Cartoon Process'  # Description of the model

    # Fields for the model
    name = fields.Char(string='Script Name', required=True)  # Name of the script
    script_path = fields.Char(string='Script Path', required=True)  # Path of the script
    python_env = fields.Char(string='Python Environment', default='',
                             help="Path to the Python interpreter (e.g., 'python3', '/path/to/venv/bin/python').")
    arguments = fields.Char(string='Script arguments')
    process_id = fields.Integer(string='Process ID')  # ID of the process
    status = fields.Selection([
        ('running', 'Running'),  # Process is running
        ('stopped', 'Stopped'),  # Process is stopped
        ('failed', 'Failed'),  # Process failed to start
    ], string='Status', default='stopped')  # Current status of the process

    def launch_script(self):
        """
        Launch a Python script using the specified Python environment and track its process ID.
        :param script_path: Path to the Python script to execute.
        :return: True if the script was launched successfully, False otherwise.
        """

        try:
            # Launch the script using the specified Python environment, arguments
            command = [self.script_path]
            if self.python_env:
                command = [self.python_env, self.script_path]
            if self.arguments:
                command += [self.arguments]

            process = subprocess.run(command, shell=True)
            # Update the process ID and status
            self.write({
                'process_id': process.pid,
                'status': 'running',
            })
            return True
        except Exception as e:
            # Log the failure and update the status
            self.write({
                'status': 'failed',
            })
            return False

    def check_process(self):
        """
        Check the status of the process using the process ID.
        :return: Current status of the process.
        """
        if self.process_id:
            # Check if the process is still running
            if psutil.pid_exists(self.process_id):
                self.write({
                    'status': 'running',
                })
            else:
                self.write({
                    'status': 'stopped',
                })
        return self.status