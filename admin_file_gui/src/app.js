import { App as H5WebApp, MockProvider } from '@h5web/app';

function AdminFileViewApp() {
  return (
    <MockProvider>
      <H5WebApp explorerOpen={true} />
    </MockProvider>
  );
}

export default AdminFileViewApp;