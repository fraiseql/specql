/**
 * Complete Frontend Integration Example for Call Service Actions
 *
 * This example demonstrates how to use the generated frontend code
 * with call_service actions for async payment processing.
 */

import React, { useState } from 'react';
import { usePlaceOrder, useProcessPaymentSync } from './generated/hooks';
import type { PlaceOrderInput, ProcessPaymentSyncInput } from './generated/types';

// Custom hook for job status monitoring
const useJobStatus = (jobId: string | null) => {
  const [status, setStatus] = useState<string | null>(null);

  React.useEffect(() => {
    if (!jobId) return;

    // Poll job status every 2 seconds
    const pollInterval = setInterval(async () => {
      try {
        // In a real app, you'd call a GraphQL query or REST endpoint
        // const response = await fetch(`/api/jobs/${jobId}/status`);
        // const data = await response.json();
        // setStatus(data.status);

        // For demo purposes, simulate status changes
        setStatus(prev => {
          if (!prev) return 'running';
          if (prev === 'running') return 'completed';
          return prev;
        });
      } catch (error) {
        console.error('Failed to poll job status:', error);
      }
    }, 2000);

    return () => clearInterval(pollInterval);
  }, [jobId]);

  return status;
};

export const OrderForm: React.FC = () => {
  const [orderData, setOrderData] = useState({
    order_number: '',
    total_amount: 0,
    customer_email: '',
  });

  const [jobId, setJobId] = useState<string | null>(null);
  const jobStatus = useJobStatus(jobId);

  // Async payment processing (recommended)
  const [placeOrder, { loading: placingOrder, error: placeOrderError }] = usePlaceOrder();

  // Sync payment processing (for immediate response)
  const [processPaymentSync, { loading: processingSync, error: syncError }] = useProcessPaymentSync();

  const handleAsyncOrder = async () => {
    try {
      const result = await placeOrder({
        variables: {
          input: orderData
        }
      });

      if (result.data?.placeOrder.success) {
        const jobId = result.data.placeOrder.job_id;
        setJobId(jobId);
        console.log('Order placed, payment job started:', jobId);

        // The generated hook already logs this, but you can add custom handling
        // The job status will be monitored by useJobStatus hook
      } else {
        console.error('Order placement failed:', result.data?.placeOrder.error);
      }
    } catch (error) {
      console.error('Order placement error:', error);
    }
  };

  const handleSyncPayment = async () => {
    try {
      const result = await processPaymentSync({
        variables: {
          input: {
            // Sync payment might need different input structure
            amount: orderData.total_amount,
            // ... other payment-specific fields
          }
        }
      });

      if (result.data?.processPaymentSync.success) {
        console.log('Payment processed synchronously');
        // No job monitoring needed for sync operations
      } else {
        console.error('Sync payment failed:', result.data?.processPaymentSync.error);
      }
    } catch (error) {
      console.error('Sync payment error:', error);
    }
  };

  return (
    <div className="order-form">
      <h2>Place Order with Payment</h2>

      <form onSubmit={(e) => e.preventDefault()}>
        <div>
          <label>Order Number:</label>
          <input
            type="text"
            value={orderData.order_number}
            onChange={(e) => setOrderData(prev => ({ ...prev, order_number: e.target.value }))}
            required
          />
        </div>

        <div>
          <label>Total Amount:</label>
          <input
            type="number"
            step="0.01"
            value={orderData.total_amount}
            onChange={(e) => setOrderData(prev => ({ ...prev, total_amount: parseFloat(e.target.value) }))}
            required
          />
        </div>

        <div>
          <label>Customer Email:</label>
          <input
            type="email"
            value={orderData.customer_email}
            onChange={(e) => setOrderData(prev => ({ ...prev, customer_email: e.target.value }))}
            required
          />
        </div>

        <div className="button-group">
          <button
            type="button"
            onClick={handleAsyncOrder}
            disabled={placingOrder}
          >
            {placingOrder ? 'Placing Order...' : 'Place Order (Async Payment)'}
          </button>

          <button
            type="button"
            onClick={handleSyncPayment}
            disabled={processingSync}
          >
            {processingSync ? 'Processing...' : 'Process Payment (Sync)'}
          </button>
        </div>
      </form>

      {/* Job Status Display */}
      {jobId && (
        <div className="job-status">
          <h3>Payment Job Status</h3>
          <p>Job ID: {jobId}</p>
          <p>Status: {jobStatus || 'Monitoring...'}</p>

          {jobStatus === 'running' && <p>🔄 Payment processing...</p>}
          {jobStatus === 'completed' && <p>✅ Payment completed successfully!</p>}
          {jobStatus === 'failed' && <p>❌ Payment failed</p>}
        </div>
      )}

      {/* Error Display */}
      {(placeOrderError || syncError) && (
        <div className="error">
          <h3>Error</h3>
          <p>{placeOrderError?.message || syncError?.message}</p>
        </div>
      )}
    </div>
  );
};

/**
 * Advanced Example: Job Status Subscription
 *
 * For real-time job status updates, you could use GraphQL subscriptions:
 */
export const JOB_STATUS_SUBSCRIPTION = gql`
  subscription OnJobStatusChange($jobId: UUID!) {
    jobStatusChanged(jobId: $jobId) {
      jobId
      status
      outputData
      errorMessage
    }
  }
`;

export const useJobStatusSubscription = (jobId: string | null) => {
  return useSubscription(JOB_STATUS_SUBSCRIPTION, {
    variables: { jobId },
    skip: !jobId,
  });
};

/**
 * Usage with subscription:
 */
export const OrderFormWithSubscription: React.FC = () => {
  // ... existing code ...

  const { data: jobData } = useJobStatusSubscription(jobId);

  // Use subscription data instead of polling
  const currentStatus = jobData?.jobStatusChanged?.status;

  // ... rest of component ...
};

/**
 * Backend GraphQL Schema Extension
 *
 * You'd need to extend your GraphQL schema to support job queries:
 */
export const JOB_QUERIES = gql`
  query GetJobStatus($jobId: UUID!) {
    job(id: $jobId) {
      id
      status
      serviceName
      operation
      createdAt
      startedAt
      completedAt
      errorMessage
    }
  }

  subscription JobStatusChanged($jobId: UUID!) {
    jobStatusChanged(jobId: $jobId) {
      jobId
      status
      outputData
      errorMessage
    }
  }
`;

/**
 * Error Handling Best Practices
 */
export const handlePaymentError = (error: any) => {
  if (error.graphQLErrors) {
    // GraphQL errors
    error.graphQLErrors.forEach((graphQLError: any) => {
      switch (graphQLError.extensions?.code) {
        case 'PAYMENT_DECLINED':
          // Handle declined payment
          break;
        case 'INSUFFICIENT_FUNDS':
          // Handle insufficient funds
          break;
        default:
          // Generic payment error
          break;
      }
    });
  } else if (error.networkError) {
    // Network error - might be temporary
    console.error('Network error during payment:', error.networkError);
  } else {
    // Other errors
    console.error('Unexpected payment error:', error);
  }
};