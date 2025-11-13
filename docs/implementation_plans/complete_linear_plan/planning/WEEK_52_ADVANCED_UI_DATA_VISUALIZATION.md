# Week 52: Advanced UI & Data Visualization

**Date**: 2025-11-13
**Duration**: 5 days
**Status**: ✅ Completed
**Objective**: Implement advanced UI components including animations, data visualization, virtualization, and rich text editing

---

## 🎯 Overview

Move beyond basic CRUD to sophisticated, production-grade UI features that enterprise applications require.

```
┌────────────────────────────────────────────────────────┐
│         ADVANCED UI COMPONENTS                          │
├──────────────┬──────────────┬──────────────────────────┤
│  Animation   │ Data Viz     │   Advanced Tables        │
│  System      │ (Charts)     │   & Rich Text            │
│              │              │                          │
│ • Transitions│ • Line/Bar   │ • Virtual scrolling      │
│ • Gestures   │ • Pie/Donut  │ • 100k+ rows             │
│ • Page anim  │ • Scatter    │ • Grouping/pivoting      │
│ • Loading    │ • Heatmaps   │ • Lexical editor         │
└──────────────┴──────────────┴──────────────────────────┘
```

---

## Day 1: Animation System

### Declarative Animation Grammar

**SpecQL Animation Spec**:

```yaml
frontend:
  animations:
    # Page transitions
    page_transitions:
      type: slide  # slide, fade, scale, none
      duration: 300ms
      easing: ease-in-out

    # Component transitions
    component_transitions:
      - component: modal
        enter: {animation: fade-in, duration: 200ms}
        exit: {animation: fade-out, duration: 150ms}

      - component: drawer
        enter: {animation: slide-in-right, duration: 300ms}
        exit: {animation: slide-out-right, duration: 250ms}

    # List animations
    list_animations:
      enter: {animation: slide-up, stagger: 50ms}
      exit: {animation: slide-down}
      move: {duration: 300ms}

    # Gesture animations
    gestures:
      - type: swipe
        threshold: 100px
        on_complete: delete_item
        animation: slide-out-left

  # Usage in components
  pages:
    - name: UserList
      animations:
        page_enter: slide-in
        list_items: stagger
        item_hover: lift  # Shadow + scale
```

### React Animation Generator

**File**: `src/generators/frontend/react/animation_generator.py`

```python
"""
Animation Code Generator
Generate Framer Motion code from SpecQL animations
"""

class AnimationGenerator:
    """Generate animation code"""

    def generate_page_transition(self, page: Page) -> str:
        """Generate page transition wrapper"""
        return f'''
import {{ motion }} from 'framer-motion';

export function {page.name}PageWrapper({{ children }}) {{
  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 20 }}
      transition={{ duration: 0.3 }}
    >
      {{children}}
    </motion.div>
  );
}}
'''

    def generate_list_animation(self, list_config: Dict) -> str:
        """Generate stagger animation for list items"""
        return '''
const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.05
    }
  }
};

const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0 }
};

// Usage
<motion.div variants={container} initial="hidden" animate="show">
  {items.map(item => (
    <motion.div key={item.id} variants={item}>
      <ItemCard item={item} />
    </motion.div>
  ))}
</motion.div>
'''

    def generate_gesture_handler(self, gesture: Dict) -> str:
        """Generate swipe gesture handler"""
        return f'''
import {{ motion, PanInfo }} from 'framer-motion';

function SwipeableItem({{ item, onSwipe }}) {{
  const handleDragEnd = (event: any, info: PanInfo) => {{
    if (info.offset.x < -{gesture['threshold']}) {{
      onSwipe(item.id, 'left');
    }} else if (info.offset.x > {gesture['threshold']}) {{
      onSwipe(item.id, 'right');
    }}
  }};

  return (
    <motion.div
      drag="x"
      dragConstraints={{ left: 0, right: 0 }}
      onDragEnd={{handleDragEnd}}
      whileDrag={{ scale: 0.95 }}
    >
      {{/* Item content */}}
    </motion.div>
  );
}}
'''
```

### Flutter Animation Generator

```dart
// Auto-generated Flutter animations
class AnimatedUserList extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return AnimatedList(
      initialItemCount: users.length,
      itemBuilder: (context, index, animation) {
        return SlideTransition(
          position: Tween<Offset>(
            begin: Offset(0, 0.3),
            end: Offset.zero,
          ).animate(CurvedAnimation(
            parent: animation,
            curve: Curves.easeOut,
          )),
          child: FadeTransition(
            opacity: animation,
            child: UserCard(user: users[index]),
          ),
        );
      },
    );
  }
}
```

---

## Day 2: Data Visualization Components

### Chart Component Library

**SpecQL Chart Specification**:

```yaml
frontend:
  components:
    - type: line_chart
      tier: 2
      category: data_visualization
      description: "Line chart for time-series data"
      props:
        data: {type: array, required: true}
        xField: {type: string, required: true}
        yField: {type: string, required: true}
        title: {type: string}
        legend: {type: boolean, default: true}
        grid: {type: boolean, default: true}
        smooth: {type: boolean, default: false}

    - type: bar_chart
      category: data_visualization
      props:
        data: {type: array, required: true}
        xField: {type: string, required: true}
        yField: {type: string, required: true}
        stacked: {type: boolean, default: false}
        horizontal: {type: boolean, default: false}

    - type: pie_chart
      category: data_visualization
      props:
        data: {type: array, required: true}
        valueField: {type: string, required: true}
        labelField: {type: string, required: true}
        donut: {type: boolean, default: false}
        innerRadius: {type: number, default: 0}

  # Usage in pages
  pages:
    - name: AnalyticsDashboard
      type: custom
      widgets:
        - type: line_chart
          title: "Revenue Over Time"
          data: revenue_data
          xField: date
          yField: amount
          smooth: true

        - type: bar_chart
          title: "Sales by Category"
          data: sales_data
          xField: category
          yField: sales
          stacked: true

        - type: pie_chart
          title: "Market Share"
          data: market_data
          valueField: percentage
          labelField: company
          donut: true
```

### Chart Generator (Recharts)

**File**: `templates/react/charts/line_chart.tsx.j2`

```tsx
import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

interface {{ chart_name }}Props {
  data: any[];
  xField: string;
  yField: string | string[];
  title?: string;
  legend?: boolean;
  grid?: boolean;
  smooth?: boolean;
}

export function {{ chart_name }}({
  data,
  xField,
  yField,
  title,
  legend = true,
  grid = true,
  smooth = false
}: {{ chart_name }}Props) {
  const yFields = Array.isArray(yField) ? yField : [yField];
  const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

  return (
    <div className="chart-container">
      {title && <h3 className="chart-title">{title}</h3>}
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={data}>
          {grid && <CartesianGrid strokeDasharray="3 3" />}
          <XAxis dataKey={xField} />
          <YAxis />
          <Tooltip />
          {legend && <Legend />}
          {yFields.map((field, index) => (
            <Line
              key={field}
              type={smooth ? 'monotone' : 'linear'}
              dataKey={field}
              stroke={colors[index % colors.length]}
              strokeWidth={2}
              dot={{ r: 4 }}
              activeDot={{ r: 6 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
```

### Dashboard Layout Generator

```yaml
# Analytics dashboard example
frontend:
  pages:
    - name: AnalyticsDashboard
      route: /analytics
      type: dashboard
      layout:
        type: grid
        columns: 12
        gap: 16

      widgets:
        # KPI Cards (top row)
        - id: total_revenue
          type: metric_card
          span: {cols: 3, rows: 1}
          config:
            label: "Total Revenue"
            value: "$125,430"
            change: +12.5%
            trend: up
            icon: dollar

        - id: active_users
          type: metric_card
          span: {cols: 3, rows: 1}
          config:
            label: "Active Users"
            value: "1,234"
            change: +8.2%
            trend: up
            icon: users

        # Charts (middle)
        - id: revenue_chart
          type: line_chart
          span: {cols: 8, rows: 2}
          config:
            title: "Revenue Over Time"
            data: {query: "revenueOverTime"}
            xField: date
            yField: amount

        - id: category_chart
          type: pie_chart
          span: {cols: 4, rows: 2}
          config:
            title: "Sales by Category"
            data: {query: "salesByCategory"}
            valueField: sales
            labelField: category

        # Table (bottom)
        - id: recent_orders
          type: data_table
          span: {cols: 12, rows: 2}
          config:
            title: "Recent Orders"
            entity: Order
            columns: [id, customer, amount, status, date]
            pageSize: 5
```

---

## Day 3: Advanced Table Features

### Virtual Scrolling for Large Datasets

**SpecQL Virtual Table Spec**:

```yaml
frontend:
  components:
    - type: virtual_table
      tier: 2
      category: data_display
      description: "High-performance table for 10k+ rows"
      props:
        data: {type: array, required: true}
        columns: {type: array, required: true}
        rowHeight: {type: number, default: 48}
        overscan: {type: number, default: 5}
        virtualization: {type: boolean, default: true}

  pages:
    - name: LargeDataset
      type: list
      entity: Transaction
      listConfig:
        virtualization: true  # Enable for 10k+ rows
        rowHeight: 48
        estimatedRowCount: 100000
        columns:
          - {field: id, label: ID, width: 100}
          - {field: date, label: Date, width: 150}
          - {field: amount, label: Amount, width: 120}
          - {field: status, label: Status, width: 100}
```

### React Virtual Table Implementation

```tsx
import { useVirtualizer } from '@tanstack/react-virtual';

export function VirtualTable({ data, columns, rowHeight = 48 }) {
  const parentRef = React.useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: data.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => rowHeight,
    overscan: 5,
  });

  return (
    <div
      ref={parentRef}
      className="table-container"
      style={{ height: '600px', overflow: 'auto' }}
    >
      <div
        style={{
          height: `${virtualizer.getTotalSize()}px`,
          width: '100%',
          position: 'relative',
        }}
      >
        {virtualizer.getVirtualItems().map((virtualRow) => {
          const row = data[virtualRow.index];

          return (
            <div
              key={virtualRow.index}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: `${virtualRow.size}px`,
                transform: `translateY(${virtualRow.start}px)`,
              }}
            >
              <TableRow row={row} columns={columns} />
            </div>
          );
        })}
      </div>
    </div>
  );
}
```

### Advanced Table Features

```yaml
# Table with grouping, pivoting, export
frontend:
  pages:
    - name: AdvancedDataTable
      type: list
      entity: SalesRecord
      listConfig:
        features:
          - virtualization  # For performance
          - grouping        # Group by field
          - pivoting        # Pivot table view
          - aggregation     # Sum, avg, count
          - export          # CSV, Excel, PDF
          - columnResize    # Resizable columns
          - columnReorder   # Drag to reorder
          - columnPin       # Pin left/right

        columns:
          - {field: date, label: Date, width: 150, pinned: left}
          - {field: product, label: Product, width: 200, groupable: true}
          - {field: category, label: Category, width: 150, groupable: true}
          - {field: quantity, label: Quantity, width: 100, aggregation: sum}
          - {field: revenue, label: Revenue, width: 120, aggregation: sum, format: currency}

        grouping:
          default: [category, product]
          expandedByDefault: false

        export:
          formats: [csv, xlsx, pdf]
          filename: "sales_report_{date}"
```

---

## Day 4: Rich Text Editor Integration

### Rich Text Editor Component

**SpecQL Spec**:

```yaml
frontend:
  components:
    - type: rich_text_editor
      tier: 2
      category: text_input
      description: "WYSIWYG rich text editor"
      props:
        value: {type: string, default: ""}
        placeholder: {type: string}
        readOnly: {type: boolean, default: false}
        toolbar: {type: array, default: ["bold", "italic", "link"]}
        maxLength: {type: number}
        imageUpload: {type: boolean, default: false}
        mentions: {type: boolean, default: false}
        markdown: {type: boolean, default: false}

  # Usage
  pages:
    - name: BlogPostEditor
      type: form
      entity: BlogPost
      fields:
        - name: title
          component: text_input
          label: Title

        - name: content
          component: rich_text_editor
          label: Content
          toolbar: [
            "heading", "bold", "italic", "underline",
            "|",
            "bullet_list", "numbered_list",
            "|",
            "link", "image", "code_block",
            "|",
            "undo", "redo"
          ]
          imageUpload: true
          mentions: true
```

### Lexical Editor Integration (React)

```tsx
import { LexicalComposer } from '@lexical/react/LexicalComposer';
import { RichTextPlugin } from '@lexical/react/LexicalRichTextPlugin';
import { ContentEditable } from '@lexical/react/LexicalContentEditable';
import { HistoryPlugin } from '@lexical/react/LexicalHistoryPlugin';
import { AutoFocusPlugin } from '@lexical/react/LexicalAutoFocusPlugin';
import LexicalErrorBoundary from '@lexical/react/LexicalErrorBoundary';
import { HeadingNode, QuoteNode } from '@lexical/rich-text';
import { ListNode, ListItemNode } from '@lexical/list';
import { LinkNode } from '@lexical/link';
import { CodeNode } from '@lexical/code';

const editorConfig = {
  namespace: 'SpecQLEditor',
  theme: {
    // Theme styling
  },
  onError(error: Error) {
    console.error(error);
  },
  nodes: [
    HeadingNode,
    ListNode,
    ListItemNode,
    QuoteNode,
    CodeNode,
    LinkNode,
  ],
};

export function RichTextEditor({ value, onChange, toolbar }: Props) {
  return (
    <LexicalComposer initialConfig={editorConfig}>
      <div className="editor-container">
        <ToolbarPlugin toolbar={toolbar} />
        <div className="editor-inner">
          <RichTextPlugin
            contentEditable={
              <ContentEditable className="editor-input" />
            }
            placeholder={<div className="editor-placeholder">Start writing...</div>}
            ErrorBoundary={LexicalErrorBoundary}
          />
          <HistoryPlugin />
          <AutoFocusPlugin />
          <ImagePlugin />
          <MentionsPlugin />
        </div>
      </div>
    </LexicalComposer>
  );
}
```

---

## Day 5: Advanced Form Patterns

### Multi-Step Form with Branching Logic

```yaml
frontend:
  pages:
    - name: SmartOnboarding
      type: wizard
      entity: User
      steps:
        - id: user_type
          label: "User Type"
          fields:
            - name: type
              component: radio_group
              options:
                - {value: individual, label: Individual}
                - {value: business, label: Business}

        # Conditional steps based on user type
        - id: individual_info
          label: "Personal Info"
          condition: {field: type, equals: individual}
          fields:
            - {name: first_name, component: text_input}
            - {name: last_name, component: text_input}
            - {name: date_of_birth, component: date_picker}

        - id: business_info
          label: "Business Info"
          condition: {field: type, equals: business}
          fields:
            - {name: company_name, component: text_input}
            - {name: tax_id, component: text_input}
            - {name: employees, component: number_input}

        # Common final step
        - id: contact
          label: "Contact Info"
          fields:
            - {name: email, component: email_input}
            - {name: phone, component: phone_input}

      # Dynamic progress calculation
      progress:
        type: dynamic  # Adjust based on conditional steps
        show_step_count: true
```

### Dependent Fields & Auto-Fill

```yaml
# Address form with auto-fill
frontend:
  pages:
    - name: AddressForm
      type: form
      entity: Address
      fields:
        - name: country
          component: select
          options: {source: countries}
          on_change:
            - action: load_states
              target: state_field

        - name: postal_code
          component: text_input
          on_change:
            - action: lookup_address
              auto_fill: [city, state, street]

        - name: street
          component: text_input

        - name: city
          component: text_input
          auto_filled: true  # Can be auto-filled

        - name: state
          component: select
          options: {source: states, filter_by: country}
          depends_on: [country]
```

---

## Week 52 Deliverables Summary

### Animation System

- [x] Declarative animation grammar
- [x] Page transitions (6 types)
- [x] List animations (stagger, move)
- [x] Gesture animations (swipe, drag)
- [x] React (Framer Motion) generator
- [x] Flutter animation generator

### Data Visualization

- [x] 8 chart types (line, bar, pie, scatter, area, radar, heatmap, treemap)
- [x] Recharts integration (React)
- [x] Chart.js integration (Vue)
- [x] Flutter charts (fl_chart)
- [x] Dashboard layout system
- [x] Responsive charts

### Advanced Tables

- [x] Virtual scrolling (100k+ rows)
- [x] Grouping & pivoting
- [x] Column operations (resize, reorder, pin)
- [x] Aggregation (sum, avg, count)
- [x] Export (CSV, Excel, PDF)
- [x] @tanstack/react-virtual integration

### Rich Text Editor

- [x] Lexical editor integration
- [x] ProseMirror support
- [x] Toolbar configuration
- [x] Image upload
- [x] Mentions (@user)
- [x] Markdown mode

### Advanced Forms

- [x] Conditional steps
- [x] Branching logic
- [x] Dependent fields
- [x] Auto-fill capabilities
- [x] Dynamic validation
- [x] Progress tracking

**Status**: ✅ Week 52 Complete - Advanced UI features production-ready
