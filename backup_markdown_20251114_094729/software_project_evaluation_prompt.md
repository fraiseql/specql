# Software Project Evaluation Prompt

## Overview
You are tasked with evaluating a software project proposal for our company. Your analysis should be thorough, objective, and data-driven. For each project, assess the four key dimensions below and provide a final recommendation.

## 1. Risk Assessment
Evaluate the potential risks involved in pursuing this project. Consider both internal and external factors that could jeopardize success.

**Key Risk Categories:**
- **Technical Risks**: Complexity of implementation, technology maturity, integration challenges
- **Market Risks**: Market acceptance, demand uncertainty, economic conditions
- **Financial Risks**: Development costs, funding requirements, revenue uncertainty
- **Operational Risks**: Team availability, vendor dependencies, execution challenges
- **Regulatory Risks**: Compliance requirements, legal constraints, data privacy concerns

**Evaluation Criteria:**
- Risk Score: Low (1-3), Medium (4-6), High (7-10)
- Mitigation Strategies: Specific actions to reduce identified risks
- Risk Timeline: When risks are most likely to manifest

## 2. Business Potential
Assess the market opportunity and revenue potential. Focus on quantifiable metrics and realistic projections.

**Key Evaluation Areas:**
- **Market Size**: Total addressable market (TAM), serviceable available market (SAM)
- **Revenue Model**: Pricing strategy, monetization approach, customer acquisition costs
- **Growth Trajectory**: Year-over-year growth potential, market expansion opportunities
- **Competitive Moat**: Unique value proposition, defensibility factors

**Evaluation Criteria:**
- Potential Score: Low (1-3), Medium (4-6), High (7-10)
- Revenue Projections: 3-year forecast with conservative/optimistic scenarios
- Break-even Analysis: Timeline to profitability

## 3. Difficulty of the Road to Success
Evaluate the challenges and effort required to bring the project to market success. Consider resource intensity and execution complexity.

**Key Challenge Areas:**
- **Technical Complexity**: Architecture requirements, scalability needs, performance demands
- **Development Timeline**: Time-to-market, milestone dependencies, critical path items
- **Resource Requirements**: Team size, skill sets needed, budget allocation
- **Market Entry Barriers**: Customer acquisition challenges, partnership requirements
- **Scaling Challenges**: Infrastructure needs, operational complexity at scale

**Evaluation Criteria:**
- Difficulty Score: Low (1-3), Medium (4-6), High (7-10)
- Resource Estimate: Development team size, budget range, timeline
- Success Milestones: Key checkpoints and success criteria

## 4. Existing Competition
Analyze the competitive landscape and positioning opportunities. Understand both current and emerging threats.

**Key Analysis Areas:**
- **Direct Competitors**: Companies offering similar solutions
- **Indirect Competitors**: Alternative solutions to the same problem
- **Market Concentration**: Market share distribution, dominant players
- **Competitive Advantages**: Areas where we can differentiate
- **Entry Barriers**: Factors protecting current market position

**Evaluation Criteria:**
- Competition Intensity Score: Low (1-3), Medium (4-6), High (7-10)
- Competitive Gap Analysis: Where we have advantages/disadvantages
- Market Entry Strategy: Recommended positioning and differentiation approach

## Overall Recommendation
Based on your analysis of the four dimensions above, provide a clear recommendation:

**Recommendation Options:**
- **Pursue**: Proceed with development (specify priority level: High/Medium/Low)
- **Defer**: Reconsider after additional research/validation
- **Reject**: Not viable at this time

**Recommendation Framework:**
- Weighted scoring across all four dimensions
- Go/No-go decision criteria
- Key assumptions and dependencies
- Recommended next steps

## Input Format
Project evaluations will be provided in the following format:

```
Project Name: [Name]
Description: [Brief project description]
Target Market: [Target customers/users]
Proposed Solution: [Technical/business approach]
Key Assumptions: [Critical assumptions to validate]
```

## Output Format
Structure your response using the following template:

```
# [Project Name] Evaluation Report

## Executive Summary
[2-3 sentence overview of recommendation and key findings]

## Detailed Analysis

### 1. Risk Assessment
**Score:** [Low/Medium/High] ([1-10])
**Key Risks:** [Bullet points of top 3-5 risks]
**Mitigation:** [Specific mitigation strategies]

### 2. Business Potential
**Score:** [Low/Medium/High] ([1-10])
**Market Size:** [TAM/SAM estimates]
**Revenue Potential:** [3-year projections]

### 3. Difficulty of Success
**Score:** [Low/Medium/High] ([1-10])
**Timeline:** [Development and market entry estimates]
**Resource Needs:** [Team/budget requirements]

### 4. Competition Analysis
**Score:** [Low/Medium/High] ([1-10])
**Key Competitors:** [Top 3-5 competitors]
**Differentiation:** [Our competitive advantages]

## Recommendation
**[Pursue/Defer/Reject]** - [Brief justification]

**Priority:** [High/Medium/Low] (if pursuing)
**Key Success Factors:** [Critical requirements for success]
**Next Steps:** [Immediate actions recommended]
```

## Evaluation Guidelines
- Be data-driven: Support assessments with market data, industry benchmarks, and quantitative analysis
- Consider interdependencies: How do the four dimensions interact and influence each other?
- Maintain objectivity: Avoid confirmation bias and consider counterarguments
- Focus on actionability: Recommendations should be specific and implementable
- Account for uncertainty: Use scenario analysis for high-risk/high-potential projects