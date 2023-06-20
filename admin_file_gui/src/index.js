import 'react-app-polyfill/stable';
import { render } from 'react-dom';

import './styles.css';

import AdminFileViewApp from "./app";

const rootElement = document.getElementById('root');
render(<AdminFileViewApp />, rootElement);
