"use client";

import clsx from "clsx";
import { motion } from "framer-motion";
import { useEffect, useState, type ReactNode } from "react";

import styles from "./finance.module.css";

type BottomSheetModalProps = {
  isOpen: boolean;
  title?: string;
  ariaLabel: string;
  onClose?: () => void;
  children: ReactNode;
  backdropClassName?: string;
  sheetClassName?: string;
  handleClassName?: string;
  titleClassName?: string;
};

export function BottomSheetModal({
  isOpen,
  title,
  ariaLabel,
  onClose,
  children,
  backdropClassName,
  sheetClassName,
  handleClassName,
  titleClassName,
}: BottomSheetModalProps) {
  const [closing, setClosing] = useState(false);

  useEffect(() => {
    if (!closing || !onClose) {
      return;
    }

    const id = window.setTimeout(() => {
      onClose();
      setClosing(false);
    }, 240);

    return () => window.clearTimeout(id);
  }, [closing, onClose]);

  if (!isOpen) {
    return null;
  }

  const handleRequestClose = () => {
    if (!onClose || closing) {
      return;
    }

    setClosing(true);
  };

  return (
    <motion.div
      className={clsx(styles.bottomSheetBackdrop, backdropClassName)}
      onClick={handleRequestClose}
      initial={{ opacity: 0 }}
      animate={{ opacity: closing ? 0 : 1 }}
      transition={{ duration: 0.2, ease: "easeOut" }}
      aria-hidden="true"
    >
      <motion.section
        className={clsx(styles.bottomSheetModal, sheetClassName)}
        onClick={(event) => event.stopPropagation()}
        initial={{ y: "100%", opacity: 0 }}
        animate={{ y: closing ? "100%" : 0, opacity: closing ? 0 : 1 }}
        drag="y"
        dragConstraints={{ top: 0, bottom: 300 }}
        dragElastic={0.15}
        onDragEnd={(_, info) => {
          if (info.offset.y > 120 || info.velocity.y > 450) {
            handleRequestClose();
          }
        }}
        transition={closing ? { duration: 0.2, ease: "easeInOut" } : { type: "spring", damping: 28, stiffness: 280 }}
        aria-label={ariaLabel}
      >
        <div className={clsx(styles.bottomSheetHandle, handleClassName)} aria-hidden="true" />
        {title ? <h2 className={clsx(styles.bottomSheetTitle, titleClassName)}>{title}</h2> : null}
        {children}
      </motion.section>
    </motion.div>
  );
}
