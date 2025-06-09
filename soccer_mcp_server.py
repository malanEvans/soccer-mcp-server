import gradio as gr

from src.tools import get_competition_info

# Create the Gradio interface
with gr.Blocks(title="Soccer Competition Lookup") as demo:
    gr.Markdown("# Soccer Competition Lookup")
    gr.Markdown("Enter a competition name to get detailed information about it.")

    with gr.Row():
        competition_input = gr.Textbox(
            label="Competition Name",
            placeholder="e.g., Premier League, Champions League",
            scale=4,
        )
        search_btn = gr.Button("Search", variant="primary")

    output = gr.Textbox(
        label="Competition Information", interactive=False, lines=20, max_lines=20
    )

    # Set up the button click handler
    search_btn.click(fn=get_competition_info, inputs=competition_input, outputs=output)

    # Also allow pressing Enter in the textbox
    competition_input.submit(
        fn=get_competition_info, inputs=competition_input, outputs=output
    )

# Run the app
if __name__ == "__main__":
    demo.launch(mcp_server=True)
