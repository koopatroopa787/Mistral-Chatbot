# Grading Templates Directory

This directory stores templates for response grading. Templates define criteria, reference answers, and context for consistent evaluation of responses.

## Template Structure

Templates are stored as JSON files with the following structure:

```json
{
  "name": "template_name",
  "criteria": {
    "criterion1": "Description of criterion1",
    "criterion2": "Description of criterion2",
    ...
  },
  "reference_answer": "Optional reference answer to compare against",
  "context": "The question or context for which this template applies"
}
```

## Usage

- Templates can be selected when grading responses in the Response Grading page
- Templates can be specified in the chat using the format `/grade [template_name]: your response`
- Templates can be created, modified, and deleted in the Response Grading page

## Default Templates

The system provides some default templates for common subjects and scenarios. You can modify these or create your own custom templates.

## Notes

- Do not manually edit these files unless you're familiar with the JSON format
- Template names should be unique and descriptive
- Templates are automatically loaded when the application starts
- New templates become available immediately after creation