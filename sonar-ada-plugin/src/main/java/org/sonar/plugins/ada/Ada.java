/*
 * Sonar Ada Plugin
 * Copyright (C) 2012, AdaCore
 */
package org.sonar.plugins.ada;

import org.sonar.api.resources.AbstractLanguage;

public class Ada extends AbstractLanguage {

    public static final Ada INSTANCE = new Ada();
    /**
     * Ada key
     */
    public static final String KEY = "ada";
    /**
     * Ada default suffixes file, as suffixes are customizable
     * no specific suffixes are mentioned.
     */
    public static final String[] DEFAULT_SUFFIXES = {};


    /**
     * Default constructor
     */
    public Ada() {
        super(KEY, "ada");
    }

    /**
     * {@inheritDoc}
     *
     * @see AbstractLanguage#getFileSuffixes()
     */
    public String[] getFileSuffixes() {
        return DEFAULT_SUFFIXES;
    }
}
