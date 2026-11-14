import { motion, useReducedMotion } from 'framer-motion';

export default function Page({ title, subtitle, actions, children }) {
  const reduce = useReducedMotion();
  return (
    <motion.div
      className="rw-page-shell"
      initial={reduce ? false : { opacity: 0, y: 12, scale: 0.992 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.28, ease: [0.23, 1, 0.32, 1] }}
    >
      <div className="page-head">
        <div>
          <h1>{title}</h1>
          {subtitle ? <p>{subtitle}</p> : null}
        </div>
        {actions ? <div className="toolbar" style={{ marginBottom: 0 }}>{actions}</div> : null}
      </div>
      {children}
    </motion.div>
  );
}
