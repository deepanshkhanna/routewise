import { motion, useReducedMotion } from 'framer-motion';

export default function Page({ title, subtitle, actions, children }) {
  const reduce = useReducedMotion();
  return (
    <motion.div
      initial={reduce ? false : { opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.28, ease: [0.16, 1, 0.3, 1] }}
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
