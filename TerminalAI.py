import ollama
import subprocess
import os
import shutil
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.live import Live
from rich.markdown import Markdown
from rich.text import Text
import json
from datetime import datetime
import textwrap

console = Console()

def get_terminal_size():
    # Get the current terminal size
    return shutil.get_terminal_size()

def clear_terminal():
    # Clear the terminal based on the operating system
    if os.name == 'nt':  # For Windows
        os.system('cls')
    else:  # For macOS and Linux
        os.system('clear')

# Filepath for storing past chats
PAST_CHATS_FILE = "past_chats.json"

def wrap_text_for_terminal(text, width=None):
    """
    Wrap text to fit terminal width, handling long lines and preserving formatting.
    Special handling for tables and structured content.
    """
    if width is None:
        terminal_width, _ = get_terminal_size()
        # Leave some margin for panel borders and padding
        width = max(50, terminal_width - 15)
    
    # If text contains table-like structures, handle them specially
    if '│' in text or '─' in text or '┌' in text or '┐' in text or '└' in text or '┘' in text:
        # This is likely a formatted table - try to preserve structure
        lines = text.split('\n')
        wrapped_lines = []
        for line in lines:
            if len(line) <= width:
                wrapped_lines.append(line)
            else:
                # For very long table lines, break at reasonable points
                if '│' in line:
                    # Try to break at table cell boundaries
                    parts = line.split('│')
                    current_line = ""
                    for i, part in enumerate(parts):
                        test_line = current_line + part + ('│' if i < len(parts) - 1 else '')
                        if len(test_line) <= width:
                            current_line = test_line
                        else:
                            if current_line:
                                wrapped_lines.append(current_line)
                            current_line = part + ('│' if i < len(parts) - 1 else '')
                    if current_line:
                        wrapped_lines.append(current_line)
                else:
                    # Fallback to regular wrapping for non-table lines
                    wrapped = textwrap.fill(line, width=width,
                                          break_long_words=True,
                                          break_on_hyphens=True)
                    wrapped_lines.append(wrapped)
        return '\n'.join(wrapped_lines)
    
    # Split text into paragraphs for regular content
    paragraphs = text.split('\n\n')
    wrapped_paragraphs = []
    
    for paragraph in paragraphs:
        # Handle code blocks and preserve their formatting
        if (paragraph.strip().startswith('```') or
            paragraph.strip().startswith('    ') or
            paragraph.strip().startswith('\t')):
            # For code blocks, wrap at character limit but preserve indentation
            lines = paragraph.split('\n')
            wrapped_lines = []
            for line in lines:
                if len(line) <= width:
                    wrapped_lines.append(line)
                else:
                    # For very long code lines, break but preserve indentation
                    indent = len(line) - len(line.lstrip())
                    indent_str = line[:indent]
                    content = line[indent:]
                    
                    # Wrap the content part
                    content_width = width - indent
                    if content_width > 20:  # Minimum reasonable width
                        wrapped = textwrap.fill(content,
                                              width=content_width,
                                              break_long_words=True,
                                              break_on_hyphens=True)
                        # Add indentation back to each line
                        indented_lines = [indent_str + wrapped_line
                                        for wrapped_line in wrapped.split('\n')]
                        wrapped_lines.extend(indented_lines)
                    else:
                        # If indent is too large, just break the line
                        wrapped_lines.append(line[:width])
                        if len(line) > width:
                            wrapped_lines.append(line[width:])
            wrapped_paragraphs.append('\n'.join(wrapped_lines))
        else:
            # Handle regular text
            lines = paragraph.split('\n')
            wrapped_lines = []
            for line in lines:
                if len(line.strip()) == 0:
                    wrapped_lines.append('')
                elif len(line) <= width:
                    wrapped_lines.append(line)
                else:
                    # Wrap long lines
                    wrapped = textwrap.fill(line, width=width,
                                          break_long_words=True,
                                          break_on_hyphens=True)
                    wrapped_lines.append(wrapped)
            wrapped_paragraphs.append('\n'.join(wrapped_lines))
    
    return '\n\n'.join(wrapped_paragraphs)

def load_past_chats():
    """Load past chats from the JSON file."""
    if not os.path.exists(PAST_CHATS_FILE):
        return []
    with open(PAST_CHATS_FILE, 'r') as file:
        return json.load(file)
    
def save_past_chats(chats):
    """Save past chats to the JSON file."""
    with open(PAST_CHATS_FILE, 'w') as file:
        json.dump(chats, file, indent=4)

def save_chat_session(conversation_history):
    """Save the current chat session."""
    past_chats = load_past_chats()
    console.print("[bold yellow]Do you want to save this chat session? (y/n)[/bold yellow]")
    save = Prompt.ask("[bold yellow]Save chat session?[/bold yellow]").lower()
    if save == 'y':
        # Ask for a custom name
        console.print("[bold yellow]Enter a custom name for this chat session (optional):[/bold yellow]")
        custom_name = Prompt.ask("[bold yellow]Chat Name[/bold yellow]", default="")
        if not custom_name.strip():
            # Default name is the current date and time
            custom_name = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        past_chats.append({
            "name": custom_name,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # Add timestamp
            "conversation": conversation_history
        })
        save_past_chats(past_chats)
        console.print(f"[bold green]Chat session saved as '{custom_name}'.[/bold green]")

def view_past_chats():
    """Enhanced view of past chat sessions with improved UI and interaction."""
    while True:
        clear_terminal()
        console.rule("[dim]Ollama Chat History[/dim]", style="dim")
        console.print("\n[bold white]Past Chat Sessions[/bold white]", justify="center")
        console.print("[dim]Type 'exit' to return to the main menu[/dim]", justify="center")
        console.print("[dim]Browse and explore your previous chat sessions[/dim]\n", justify="center")

        # Load past chats
        past_chats = load_past_chats()
        
        if not past_chats:
            # Styled panel for no chats
            no_chats_panel = Panel(
                "[bold yellow]No past chat sessions found.[/bold yellow]\n"
                "[dim]Start a new chat to create your first session![/dim]",
                title="[bold red]Empty Chat History[/bold red]",
                border_style="red",
                padding=(1, 2)
            )
            console.print(no_chats_panel, justify="center")
            console.print("[dim]Press Enter to return to the main menu.[/dim]", justify="center")
            input()
            return

        # Create a table for past chats
        table = Table(title="[bold cyan]Saved Chat Sessions[/bold cyan]")
        table.add_column("No.", style="dim", width=4, justify="center")
        table.add_column("Chat Name", style="bold cyan", justify="center")
        table.add_column("Date", style="magenta", justify="center")
        table.add_column("First Message Preview", style="dim", justify="center")

        for i, chat in enumerate(past_chats, 1):
            # Truncate preview if too long
            preview = chat['conversation'][0]['content'][:50] + '...' if chat['conversation'] else "N/A"
            table.add_row(
                str(i),
                chat['name'],
                chat.get('timestamp', 'N/A'),
                preview
            )

        console.print(table, justify="center")
        console.print()

        # Chat selection and viewing
        while True:
            choice = Prompt.ask("[bold green]Enter chat number to view (or 'exit' to return)[/bold green]")
            
            if choice.lower() == 'exit':
                return

            try:
                choice = int(choice)
                if 1 <= choice <= len(past_chats):
                    # Selected chat details panel
                    selected_chat = past_chats[choice - 1]
                    details_panel = Panel(
                        f"[bold white]Chat Details[/bold white]\n"
                        f"[cyan]Name[/cyan]: {selected_chat['name']}\n"
                        f"[cyan]Timestamp[/cyan]: {selected_chat.get('timestamp', 'N/A')}\n"
                        f"[dim]Total Messages[/dim]: {len(selected_chat['conversation'])}",
                        title="[bold yellow]Chat Overview[/bold yellow]",
                        border_style="yellow",
                        padding=(1, 2)
                    )
                    console.print(details_panel)

                    # Chat conversation display with proper wrapping
                    console.print("\n[bold]Chat Conversation:[/bold]")
                    for message in selected_chat['conversation']:
                        role = message['role']
                        content = message['content']
                        # Wrap content to fit terminal
                        wrapped_content = wrap_text_for_terminal(content)
                        # Colorize based on role
                        role_color = "green" if role == 'user' else "blue"
                        console.print(f"[bold {role_color}]{role.capitalize()}:[/bold {role_color}] {wrapped_content}")

                    # Options after viewing
                    console.print("\n[dim]Options:[/dim]")
                    option = Prompt.ask("[bold yellow]Would you like to (d)elete this chat, (c)ontinue viewing, or (e)xit[/bold yellow]").lower()
                    
                    if option == 'd':
                        # Delete confirmation
                        confirm = Prompt.ask("[bold red]Are you sure you want to delete this chat? (y/n)[/bold red]").lower()
                        if confirm == 'y':
                            past_chats.pop(choice - 1)
                            save_past_chats(past_chats)
                            console.print("[bold green]Chat deleted successfully![/bold green]")
                            break  # Return to chat list
                    elif option == 'e':
                        return
                    # 'c' or any other input continues viewing
                else:
                    console.print("[bold red]Invalid choice. Please enter a number from the list.[/bold red]")
            except ValueError:
                console.print("[bold red]Invalid input. Please enter a number or 'exit'.[/bold red]")

def sanitize_conversation_history(conversation_history, selected_model):
    """
    Sanitize conversation history to ensure correct role types.
    
    Args:
        conversation_history (list): List of conversation messages
        selected_model (str): Name of the selected model
    
    Returns:
        list: Sanitized conversation history
    """
    sanitized_history = []
    for message in conversation_history:
        # Create a copy of the message to avoid modifying the original
        sanitized_message = message.copy()
        
        # Normalize the role
        if sanitized_message['role'] not in ['user', 'assistant', 'system', 'tool']:
            # If role is not valid, set to 'user' for user messages
            # and 'assistant' for model messages
            if sanitized_message['role'] == 'user':
                sanitized_message['role'] = 'user'
            else:
                sanitized_message['role'] = 'assistant'
        
        sanitized_history.append(sanitized_message)
    
    return sanitized_history

def get_available_models():
    # Fetch available Ollama model
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, check=True)
        models = result.stdout.splitlines()[1:]  # Skip the header line
        parsed_models = []
        for model in models:
            if model.strip():
                parts = model.split()
                parsed_models.append({
                    'name': parts[0],
                    'size': ' '.join(parts[2:4]) if len(parts) > 3 else 'N/A'
                })
        return parsed_models
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]Error fetching models: {e}[/bold red]")
        return []

def display_models_table(models):
    """Display models in a table."""
    # Create a Rich Table
    table = Table(title="[bold cyan]Available AI Models[/bold cyan]")
    
    # Add columns
    table.add_column("No.", style="dim", width=4, justify="center")
    table.add_column("Model Name", style="bold cyan", justify="center")
    table.add_column("Size", style="magenta", justify="center")
    
    # Add rows
    for i, model in enumerate(models, 1):
        table.add_row(
            str(i),
            model['name'],
            model['size']
        )
    
    return table

def format_markdown_for_terminal(markdown_text):
    """
    Convert markdown to a terminal-friendly format with improved formatting and text wrapping.
    
    This function handles:
    - Converting bullet points to actual bullet points
    - Bold and italic formatting
    - Code blocks
    - Headings
    """
    # Get terminal width and calculate safe content width
    terminal_width, _ = get_terminal_size()
    # Account for panel borders, padding, and some safety margin
    safe_width = max(50, terminal_width - 15)
    
    # Wrap the text first to prevent overflow
    wrapped_text = wrap_text_for_terminal(markdown_text, width=safe_width)
    
    # Use Rich's Markdown renderer for terminal output
    markdown_obj = Markdown(wrapped_text)
    
    # Force width constraint on the markdown object
    markdown_obj.markup = True
    
    return markdown_obj

def get_multi_line_input():
    """
    Capture multi-line input when user enters /multi-start and /multi-end.
    Returns the collected multi-line input.
    """
    console.print("[bold yellow]Entered multi-line input mode. Use '/multi-end' to complete input.[/bold yellow]")
    lines = []
    while True:
        line = input()
        if line.strip() == '/multi-end':
            break
        lines.append(line)
    return '\n'.join(lines)

def pull_model():
    """Handle the model pulling process with improved user experience and encoding handling."""
    while True:
        clear_terminal()
        console.rule("[dim]Ollama Model Pull[/dim]", style="dim")
        console.print("\n[bold white]Model Pulling Page[/bold white]", justify="center")
        console.print("[dim]Type 'exit' to return to the main menu[/dim]", justify="center")
        console.print("[dim]Enter a model name to pull from Ollama.[/dim]", justify="center")
        console.print("[dim]Examples: 'llama3.2'; 'deepseek-r1'; 'gemma3'[/dim]\n", justify="center")

        # Predefined list of recommended models for easier selection
        recommended_models = [
            "gemma3", "deepseek-r1", "phi4", "llama3.2",
            "llama2-uncensored"
        ]

        # Display recommended models in a grid inside a box
        recommended_table = Table(show_header=False, box=None)
        recommended_table.add_column(justify="center")
        recommended_table.add_column(justify="center")

        # Split recommended models into two columns
        for i in range(0, len(recommended_models), 2):
            col1 = recommended_models[i]
            col2 = recommended_models[i+1] if i+1 < len(recommended_models) else ""
            recommended_table.add_row(
                f"[cyan]{col1}[/cyan]",
                f"[cyan]{col2}[/cyan]"
            )

        # Wrap the table in a Panel
        recommended_panel = Panel(
            recommended_table,
            title="[bold green]Recommended Models[/bold green]",
        )

        console.print(recommended_panel, justify="center")
        console.print()

        # Get model name with intelligent prompting
        while True:
            model_name = Prompt.ask("[bold green]Model Name[/bold green]", default="", show_default=False)
            
            if model_name.lower() in ['exit', '']:
                return  # Exit the pull model page and return to the main menu

            # Model parameter selection
            model_size = Prompt.ask(
                "[bold green]Model Parameter (optional)[/bold green]",
                default="latest",
                show_default=False
            )
            model_size = model_size.strip() if model_size.strip() else "latest"

            # Construct full model identifier
            full_model = f"{model_name}:{model_size}"

            # Confirmation panel
            confirm_panel = Panel(
                f"[bold white]Confirm Model Pull:[/bold white]\n"
                f"[cyan]Model[/cyan]: {full_model}",
                title="[bold yellow]Confirmation[/bold yellow]",
                border_style="yellow",
                padding=(1, 2)
            )
            console.print(confirm_panel)

            # Confirm pull
            confirm = Prompt.ask("[bold yellow]Confirm pull? (y/n)[/bold yellow]").lower()
            if confirm != 'y':
                console.print("[bold red]Model pull cancelled.[/bold red]")
                break

            console.print(f"[bold green]Pulling {full_model}...[/bold green]", justify="center")
            
            # Simulate pulling the model with a rich loading experience
            with Live(console=console, refresh_per_second=10) as live:
                try:
                    pulling_panel = Panel(
                        "[bold yellow]Downloading model...[/bold yellow]\n"
                        "[dim]This may take several minutes depending on model size.[/dim]",
                        title="[bold cyan]Pulling Model[/bold cyan]",
                        border_style="cyan",
                        padding=(1, 2),
                        expand=False
                    )
                    live.update(pulling_panel)

                    # Execute the `ollama pull` command with explicit error handling and encoding
                    result = subprocess.run(
                        ['ollama', 'pull', full_model],
                        capture_output=True,
                        text=True,
                        encoding='utf-8',  # Explicitly use UTF-8 encoding
                        errors='replace',  # Replace undecodable bytes
                        check=True
                    )
                    
                    # Success panel
                    pulling_panel = Panel(
                        f"[bold green]Successfully pulled {full_model}![/bold green]\n"
                        "[dim]Model is now available for chat.[/dim]",
                        title="[bold green]Pull Complete[/bold green]",
                        border_style="green",
                        padding=(1, 2),
                        expand=False
                    )
                    live.update(pulling_panel)

                except subprocess.CalledProcessError as e:
                    # Error handling panel
                    error_panel = Panel(
                        "[dim]Possible reasons:\n"
                        "- Invalid model name\n"
                        "- Network issues\n"
                        "- Ollama service not running[/dim]",
                        title="[bold red]Pull Failed[/bold red]",
                        border_style="red",
                        padding=(1, 2),
                        expand=False
                    )
                    live.update(error_panel)

            # Ask if the user wants to pull another model
            another = Prompt.ask("[bold yellow]Pull another model? (y/n)[/bold yellow]").lower()
            if another != 'y':
                return  # Exit the pull model page

def remove_model():
    """Handle the model removal process with improved user experience and error handling."""
    while True:
        clear_terminal()
        console.rule("[dim]Ollama Model Removal[/dim]", style="dim")
        console.print("\n[bold white]Model Removal Page[/bold white]", justify="center")
        console.print("[dim]Type 'exit' to return to the main menu[/dim]", justify="center")
        console.print("[dim]Select a model to remove from your local Ollama library.[/dim]\n", justify="center")

        # Fetch current models
        models = get_available_models()
        
        if not models:
            console.print("[bold red]No models available to remove.[/bold red]", justify="center")
            console.print("[dim]Press Enter to return to the main menu.[/dim]", justify="center")
            input()
            return

        # Display models in a table with selection numbers
        remove_table = Table(title="[bold cyan]Available Models[/bold cyan]")
        remove_table.add_column("No.", style="dim", width=4, justify="center")
        remove_table.add_column("Model Name", style="bold cyan", justify="center")
        remove_table.add_column("Size", style="magenta", justify="center")
        
        for i, model in enumerate(models, 1):
            remove_table.add_row(
                str(i),
                model['name'],
                model['size']
            )
        
        console.print(remove_table, justify="center")
        console.print()

        # Model selection
        while True:
            choice = Prompt.ask("[bold bright_red]Enter the number of the model to remove[/bold bright_red]")
            
            if choice.lower() in ['exit', '']:
                return  # Exit the remove model page
            
            try:
                choice = int(choice)
                if 1 <= choice <= len(models):
                    selected_model = models[choice - 1]['name']
                    break
                else:
                    console.print("[bold red]Invalid choice. Please enter a number from the list.[/bold red]", justify="center")
            except ValueError:
                console.print()  # Add spacing
                console.print("[bold red]Invalid input. Please enter a number.[/bold red]", justify="center")
                console.print() # Add spacing

        # Confirmation panel
        confirm_panel = Panel(
            f"[bold white]Confirm Model Removal:[/bold white]\n"
            f"[red]Model[/red]: {selected_model}",
            title="[bold yellow]Confirmation[/bold yellow]",
            border_style="bright_red",
            padding=(1, 2)
        )
        console.print(confirm_panel)

        # Final confirmation
        confirm = Prompt.ask("[bold bright_red]Are you sure you want to remove this model? (y/n)[/bold bright_red]").lower()
        if confirm != 'y':
            console.print("[bold yellow]Model removal cancelled.[/bold yellow]")
            continue

        # Model removal process
        console.print(f"[bold bright_red]Removing {selected_model}...[/bold bright_red]", justify="center")
        
        # Simulate model removal with rich loading experience
        with Live(console=console, refresh_per_second=10) as live:
            try:
                removing_panel = Panel(
                    "[bold yellow]Removing model...[/bold yellow]\n"
                    "[dim]This may take a moment.[/dim]",
                    title="[bold bright_red]Removing Model[/bold bright_red]",
                    border_style="bright_red",
                    padding=(1, 2),
                    expand=False
                )
                live.update(removing_panel)

                # Execute the `ollama rm` command with explicit error handling and encoding
                result = subprocess.run(
                    ['ollama', 'rm', selected_model],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',  # Explicitly use UTF-8 encoding
                    errors='replace',  # Replace undecodable bytes
                    check=True
                )
                
                # Success panel
                removing_panel = Panel(
                    f"[bold green]Successfully removed {selected_model}![/bold green]\n"
                    "[dim]Model has been deleted from your local library.[/dim]",
                    title="[bold green]Removal Complete[/bold green]",
                    border_style="green",
                    padding=(1, 2),
                    expand=False
                )
                live.update(removing_panel)

            except subprocess.CalledProcessError as e:
                # Error handling panel
                error_panel = Panel(
                    "[dim]Possible reasons:\n"
                    "- Model may not exist\n"
                    "- Insufficient permissions\n"
                    "- Ollama service issues[/dim]",
                    title="[bold red]Removal Failed[/bold red]",
                    border_style="red",
                    padding=(1, 2),
                    expand=False
                )
                live.update(error_panel)

        # Ask if the user wants to remove another model
        another = Prompt.ask("[bold yellow]Remove another model? (y/n)[/bold yellow]").lower()
        if another != 'y':
            return  # Exit the remove model page

# Update the main menu to include the 'view' option
def start_chat():
    while True:
        # Main chat page
        clear_terminal()
        terminal_width, _ = get_terminal_size()

        # Welcome banner
        console.rule("[dim]AI Terminal[dim]", style="dim")
        console.print()
        console.print("[bold white]Welcome to the Ollama AI Terminal![/bold white]", justify="center")
        console.print()
        console.print("[dim]Commands:[dim]", justify="center")
        console.print("[dim]Type 'exit' to quit the program[/dim]", justify="center")
        console.print("[dim]Type 'pull' to pull a new model[/dim]", justify="center")
        console.print("[dim]Type 'remove' to remove a model[/dim]", justify="center")
        console.print("[dim]Type 'view' to view past chat sessions[/dim]", justify="center")
        console.print("[dim]When chatting, '/multi-start' to enter multi-line input mode[/dim]\n", justify="center")

        # Fetch and display available models
        models = get_available_models()
        if not models:
            console.print("[bold red]No models available. Pulling first model...[/bold red]", justify="center")
            pull_model()  # Call pull_model without arguments
            continue

        # Display models in a table
        console.print(display_models_table(models), justify="center")

        # Prompt for model selection or actions
        while True:
            console.print()  # Add spacing
            choice = Prompt.ask("[bold yellow]Enter the number of the model you would like to chat with[/bold yellow]")
            
            if choice.lower() == 'exit':
                console.print()  # Add spacing
                console.print("[bold sea_green1]Goodbye![/bold sea_green1]", justify="center")
                console.print()  # Add spacing
                return
            
            if choice.lower() == 'pull':
                pull_model()  # Call pull_model without arguments
                # Restart the main menu after pulling models
                break
            
            if choice.lower() == 'remove':
                remove_model()  # Call the new remove_model function
                # Restart the main menu after removing models
                break
            
            if choice.lower() == 'view':
                view_past_chats()  # Call the view_past_chats function
                # Restart the main menu after viewing chats
                break
            
            try:
                choice_num = int(choice)
                if 1 <= choice_num <= len(models):
                    selected_model = models[choice_num - 1]['name']
                    break
                else:
                    console.print()  # Add spacing
                    console.print("[bold red]Invalid choice. Please enter a number from the list.[/bold red]", justify="center")
            except ValueError:
                console.print()  # Add spacing
                console.print("[bold red]- Invalid input -\nPlease Enter a Number or Type:\n'exit' to quit\n'pull' to pull a new model\n'remove' to remove a model\n'view' to view past chats[/bold red]", justify="center")

        # If the user chooses to pull or remove a model, restart the main menu
        if choice.lower() in ['pull', 'remove', 'view']:
            continue

        console.print()  # Add spacing
        # Display the selected model
        console.rule(f"[bold green]Chatting with {selected_model}[/bold green]", style="green", align="center")

        conversation_history = []

        # Modify the chat loop to use the sanitization function
        while True:
            # User input
            user_input = Prompt.ask("[bold green]You[/bold green]")
            
            if user_input.lower() == 'exit':
                break

            # Check for multi-line input
            if user_input == '/multi-start':
                user_input = get_multi_line_input()

            conversation_history.append({'role': 'user', 'content': user_input})

            # Sanitize conversation history before sending to Ollama
            sanitized_history = sanitize_conversation_history(conversation_history, selected_model)

            # Prepare for streaming response
            full_response = ""

            # Create a panel for the response
            with Live(console=console, refresh_per_second=10) as live:
                # Streaming response
                response_panel = Panel(
                    "Thinking...",
                    title=f"[bold dark_olive_green1]{selected_model} Response[/bold dark_olive_green1]",
                    border_style="dark_olive_green1",
                    padding=(1, 2),
                    expand=False
                )
                live.update(response_panel)

                # Stream the response
                first_chunk = True
                try:
                    for chunk in ollama.chat(
                        model=selected_model,
                        messages=sanitized_history,
                        stream=True
                    ):
                        if 'message' in chunk:
                            # If it's the first chunk, switch from loading to content
                            if first_chunk:
                                first_chunk = False
                                full_response = ""

                            # Append the chunk to full response
                            chunk_content = chunk['message'].get('content', '')
                            full_response += chunk_content

                            # Get terminal width and set panel width constraints
                            terminal_width, _ = get_terminal_size()
                            panel_width = min(terminal_width - 4, 120)  # Max width with safety margin

                            # Update the display with current response
                            response_panel = Panel(
                                format_markdown_for_terminal(full_response),
                                title=f"[bold pink3]{selected_model} Response[/bold pink3]",
                                border_style="pink3",
                                padding=(1, 2),
                                expand=False,
                                width=panel_width
                            )
                            live.update(response_panel)

                except Exception as e:
                    # Comprehensive error handling
                    error_panel = Panel(
                        f"[bold red]An error occurred during chat:[/bold red]\n"
                        f"[dim]{str(e)}[/dim]\n\n"
                        "[yellow]Possible reasons:\n"
                        "- Model connection issue\n"
                        "- Ollama service not running\n"
                        "- Invalid conversation history[/yellow]",
                        title="[bold bright_red]Chat Error[/bold bright_red]",
                        border_style="bright_red",
                        padding=(1, 2)
                    )
                    live.update(error_panel)
                    
                    # Optionally, reset the conversation history
                    conversation_history = []
                    
                    # Wait for user acknowledgment
                    console.print("[dim]Press Enter to continue...[/dim]")
                    input()
                    break

            # Add full response to conversation history with correct role
            conversation_history.append({'role': 'assistant', 'content': full_response})

        # Save the chat session
        save_chat_session(conversation_history)

        # Ask the user if they want to choose a different model
        while True:
            console.print()  # Add spacing
            choice = Prompt.ask("[bold yellow]Would you like to return to the main menu? (y/n)[/bold yellow]").lower()
            if choice == 'n':
                console.print()  # Add spacing
                console.print("[bold sea_green1]Goodbye![/bold sea_green1]", justify="center")
                console.print()  # Add spacing
                return
            elif choice == 'y':
                break
            else:
                console.print()  # Add spacing
                console.print("[bold red]Invalid choice. Please enter 'y' or 'n'.[/bold red]", justify="center")

if __name__ == '__main__':
    try:
        start_chat()
    except KeyboardInterrupt:
        console.print("\n[bold sea_green1]Manual shutdown...Goodbye![/bold sea_green1]", justify="center")
        console.print() # Add spacing
