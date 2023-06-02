import { App as H5WebApp, H5GroveProvider } from '@h5web/app';

function AdminFileViewApp() {

  const query = new URLSearchParams(window.location.search);
  const file = query.get('file');

  if (!file) {
    return (
      <p>
        Provide a file name by adding
        <pre>?file=...</pre>
        to the URL.
      </p>
    );
  }



  return (
    <H5GroveProvider
      url='http://localhost:5000'
      filepath={file}
      axiosConfig={{ params: { file } }}
    >
      <H5WebApp explorerOpen={true} />
    </H5GroveProvider>
  );
}

export default AdminFileViewApp;