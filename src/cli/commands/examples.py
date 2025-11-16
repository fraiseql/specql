"""
SpecQL Examples Command

Provides built-in examples of SpecQL YAML specifications for common use cases.
"""

import click


EXAMPLES = {
    "simple-entity": {
        "description": "Simple entity with basic fields",
        "yaml": """entity: Contact
schema: crm

fields:
  name: text
  email: email
  phone: text""",
    },
    "with-relationships": {
        "description": "Entity with foreign key relationships",
        "yaml": """entity: Contact
schema: crm

fields:
  name: text
  email: email
  company: ref(Company)  # Foreign key to Company""",
    },
    "with-actions": {
        "description": "Entity with business logic actions",
        "yaml": """entity: Contact
schema: crm

fields:
  name: text
  status: enum(lead, customer)
actions:
  - name: convert_to_customer
    steps:
      - validate: status = 'lead'
      - update: Contact SET status = 'customer'""",
    },
    "with-enums": {
        "description": "Entity with enumerated fields",
        "yaml": """entity: Product
schema: ecommerce

fields:
  name: text
  category: enum(electronics, clothing, books, home)
  status: enum(active, discontinued, out_of_stock)
  price: decimal""",
    },
    "with-timestamps": {
        "description": "Entity with timestamp fields",
        "yaml": """entity: Order
schema: ecommerce

fields:
  customer: ref(Customer)
  order_date: timestamp
  status: enum(pending, confirmed, shipped, delivered)
  total_amount: decimal""",
    },
    "with-json": {
        "description": "Entity with JSON metadata field",
        "yaml": """entity: User
schema: auth

fields:
  username: text
  email: email
  preferences: json  # Store user preferences as JSON
  metadata: json     # Additional user data""",
    },
    "blog-post": {
        "description": "Blog post with author relationship",
        "yaml": """entity: Post
schema: blog

fields:
  title: text
  slug: text
  content: text
  author: ref(Author)
  published_at: timestamp
  status: enum(draft, published, archived)

indexes:
  - fields: [slug]
    unique: true""",
    },
    "ecommerce-order": {
        "description": "E-commerce order with complex relationships",
        "yaml": """entity: Order
schema: ecommerce

fields:
  customer: ref(Customer)
  order_number: text
  order_date: timestamp
  status: enum(pending, paid, shipped, delivered, cancelled)
  total_amount: decimal
  shipping_address: json

actions:
  - name: mark_as_paid
    steps:
      - validate: status = 'pending'
      - update: Order SET status = 'paid'

  - name: ship_order
    steps:
      - validate: status = 'paid'
      - update: Order SET status = 'shipped'""",
    },
}


@click.command()
@click.argument("example_name", required=False)
@click.option("--list", is_flag=True, help="List all available examples")
def examples(example_name, list):
    """Show example code and usage patterns."""

    if list:
        click.echo("📚 Available SpecQL Examples:\n")
        for name, data in EXAMPLES.items():
            click.echo(f"  {name}: {data['description']}")
        click.echo("\nUsage: specql examples <example-name>")
        click.echo("       specql examples --list")
        return

    if not example_name:
        click.echo("❌ Please specify an example name or use --list")
        click.echo("\nAvailable examples:")
        for name, data in EXAMPLES.items():
            click.echo(f"  • {name}: {data['description']}")
        click.echo("\nUsage: specql examples <example-name>")
        return

    if example_name not in EXAMPLES:
        click.echo(f"❌ Unknown example: '{example_name}'")
        click.echo("\nAvailable examples:")
        for name, data in EXAMPLES.items():
            click.echo(f"  • {name}: {data['description']}")
        click.echo("\nUse 'specql examples --list' for more details")
        return

    example = EXAMPLES[example_name]
    click.echo(f"📖 Example: {example_name}")
    click.echo(f"📝 Description: {example['description']}\n")
    click.echo("YAML Specification:")
    click.echo("=" * 50)
    click.echo(example["yaml"])
    click.echo("=" * 50)
    click.echo("\n💡 To generate code from this example:")
    click.echo(f"   1. Save the YAML above to a file (e.g., {example_name}.yaml)")
    click.echo(f"   2. Run: specql generate {example_name}.yaml")
    click.echo("   3. Check the generated files in the output directory")
